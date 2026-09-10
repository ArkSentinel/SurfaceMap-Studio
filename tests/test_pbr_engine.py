"""
Unit tests for PBR Generation Engine, Presets, and Exporter
"""

import os
import shutil
import tempfile
import unittest
import numpy as np
from PIL import Image

from pbr_studio.core.pbr_engine import PBREngine, PBRMapSettings
from pbr_studio.core.presets import PresetManager, DEFAULT_PRESETS
from pbr_studio.core.exporter import PBRExporter, ExportConfig


class TestPBREngine(unittest.TestCase):

    def setUp(self):
        self.settings = PBRMapSettings()
        # Create a synthetic 128x128 test image
        self.h, self.w = 128, 128
        y, x = np.mgrid[0:self.h, 0:self.w]
        arr = np.sin(x * 0.1) * np.cos(y * 0.1) * 0.5 + 0.5
        self.test_img = np.repeat(arr[:, :, np.newaxis], 3, axis=2).astype(np.float32)

    def test_height_map_generation(self):
        height = PBREngine.generate_height_map(self.test_img, self.settings)
        self.assertEqual(height.shape, (self.h, self.w))
        self.assertTrue(np.all(height >= 0.0) and np.all(height <= 1.0))
        self.assertAlmostEqual(float(np.mean(height)), 0.5, delta=0.25)

    def test_normal_map_generation(self):
        height = PBREngine.generate_height_map(self.test_img, self.settings)
        normal = PBREngine.generate_normal_map(height, self.test_img, self.settings)
        self.assertEqual(normal.shape, (self.h, self.w, 3))
        self.assertTrue(np.all(normal >= 0.0) and np.all(normal <= 1.0))
        # Blue channel (Z) should generally be dominant pointing outwards (> 0.5)
        self.assertTrue(np.mean(normal[:, :, 2]) > 0.5)

    def test_roughness_map_generation(self):
        height = PBREngine.generate_height_map(self.test_img, self.settings)
        roughness = PBREngine.generate_roughness_map(height, self.test_img, self.settings)
        self.assertEqual(roughness.shape, (self.h, self.w))
        self.assertTrue(np.all(roughness >= 0.0) and np.all(roughness <= 1.0))

    def test_metallic_map_generation(self):
        metallic = PBREngine.generate_metallic_map(self.test_img, self.settings)
        self.assertEqual(metallic.shape, (self.h, self.w))
        self.assertTrue(np.all(metallic >= 0.0) and np.all(metallic <= 1.0))

    def test_ao_map_generation(self):
        height = PBREngine.generate_height_map(self.test_img, self.settings)
        ao = PBREngine.generate_ao_map(height, self.settings)
        self.assertEqual(ao.shape, (self.h, self.w))
        self.assertTrue(np.all(ao >= 0.0) and np.all(ao <= 1.0))

    def test_orm_packing(self):
        ao = np.full((self.h, self.w), 1.0, dtype=np.float32)
        rough = np.full((self.h, self.w), 0.5, dtype=np.float32)
        metal = np.full((self.h, self.w), 0.2, dtype=np.float32)
        orm = PBREngine.generate_orm_packed(ao, rough, metal)
        self.assertEqual(orm.shape, (self.h, self.w, 3))
        self.assertTrue(np.allclose(orm[:, :, 0], 1.0))
        self.assertTrue(np.allclose(orm[:, :, 1], 0.5))
        self.assertTrue(np.allclose(orm[:, :, 2], 0.2))

    def test_presets(self):
        names = PresetManager.get_preset_names()
        self.assertTrue(len(names) > 0)
        for name in names:
            ok = PresetManager.apply_preset(self.settings, name)
            self.assertTrue(ok)

    def test_exporter(self):
        temp_dir = tempfile.mkdtemp()
        try:
            maps = PBREngine.generate_all_maps(self.test_img, self.settings)
            config = ExportConfig()
            config.output_directory = temp_dir
            config.base_name = "test_material"
            config.format = "PNG"

            saved = PBRExporter.export_all_maps(maps, config)
            self.assertTrue(len(saved) >= 6)
            for k, fpath in saved.items():
                self.assertTrue(os.path.exists(fpath))
                self.assertGreater(os.path.getsize(fpath), 0)
        finally:
            shutil.rmtree(temp_dir)

    def test_3d_pbr_render(self):
        from pbr_studio.ui.preview_3d import PBRShaderRenderer
        maps = PBREngine.generate_all_maps(self.test_img, self.settings)
        rgb = PBRShaderRenderer.render_sphere_pbr(
            res=128,
            rot_y=0.5,
            rot_x=0.2,
            light_dir=np.array([0.5, 0.8, 1.0], dtype=np.float32),
            albedo_map=maps["albedo"],
            normal_map=maps["normal"],
            roughness_map=maps["roughness"],
            metallic_map=maps["metallic"],
            ao_map=maps["ao"]
        )
        self.assertEqual(rgb.shape, (128, 128, 3))
        self.assertTrue(np.all(rgb >= 0.0) and np.all(rgb <= 1.0))

    def test_project_manager(self):
        from pbr_studio.core.projects import ProjectTarget, ProjectManager
        projects = ProjectManager.load_projects()
        self.assertGreaterEqual(len(projects), 1)
        p = projects[0]
        self.assertIsNotNone(p.name)
        self.assertIsNotNone(p.destination_path)
        d = p.to_dict()
        p2 = ProjectTarget.from_dict(d)
        self.assertEqual(p.name, p2.name)

    def test_batch_manager(self):
        from pbr_studio.core.batch_manager import BatchManager
        from pbr_studio.core.projects import ProjectTarget
        
        temp_dir = tempfile.mkdtemp()
        try:
            # Create 2 test image files
            img1_path = os.path.join(temp_dir, "tex1.png")
            img2_path = os.path.join(temp_dir, "tex2.png")
            Image.fromarray((self.test_img * 255).astype(np.uint8)).save(img1_path)
            Image.fromarray((self.test_img * 255).astype(np.uint8)).save(img2_path)

            bm = BatchManager()
            added = bm.add_files([img1_path, img2_path])
            self.assertEqual(len(added), 2)
            self.assertEqual(len(bm.items), 2)

            bm.process_all()
            for item in bm.items:
                self.assertEqual(item.status, "Generado")
                self.assertIn("normal", item.generated_maps)

            proj = ProjectTarget("TestProj", os.path.join(temp_dir, "output"), "Godot 4")
            count = bm.export_all_to_project(proj)
            self.assertEqual(count, 2)
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "output", "tex1")))
            self.assertTrue(os.path.exists(os.path.join(temp_dir, "output", "tex2")))
        finally:
            shutil.rmtree(temp_dir)

    def test_avif_read_and_export(self):
        temp_dir = tempfile.mkdtemp()
        try:
            avif_path = os.path.join(temp_dir, "test_texture.avif")
            pil_img = Image.fromarray((self.test_img * 255).astype(np.uint8))
            pil_img.save(avif_path, format="AVIF")
            self.assertTrue(os.path.exists(avif_path))

            # Test load
            loaded_arr = PBREngine.load_image(avif_path)
            self.assertEqual(loaded_arr.shape, (self.h, self.w, 3))

            # Test export to AVIF
            config = ExportConfig()
            config.output_directory = temp_dir
            config.base_name = "test_avif_out"
            config.format = "AVIF"
            
            saved_path = PBRExporter.export_single_map("normal", loaded_arr, config)
            self.assertTrue(os.path.exists(saved_path))
            self.assertTrue(saved_path.endswith(".avif"))
        finally:
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    unittest.main()
