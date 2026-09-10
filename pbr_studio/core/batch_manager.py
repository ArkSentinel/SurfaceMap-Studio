"""
Batch Multi-Texture Processor
Handles queuing multiple textures, per-material settings/presets, and bulk PBR generation and export.
"""

import os
import uuid
from typing import List, Dict, Optional, Callable
import numpy as np
from PIL import Image

from .pbr_engine import PBREngine, PBRMapSettings
from .presets import PresetManager
from .exporter import PBRExporter, ExportConfig
from .projects import ProjectTarget


class BatchMaterialItem:
    """Represents a single texture file in the batch queue."""
    def __init__(self, file_path: str, default_preset: str = "Piedra / Roca (Stone / Rock)"):
        self.id: str = str(uuid.uuid4())[:8]
        self.file_path: str = file_path
        self.name: str = os.path.splitext(os.path.basename(file_path))[0]
        self.settings: PBRMapSettings = PBRMapSettings()
        self.preset_name: str = default_preset
        
        # Apply initial preset
        PresetManager.apply_preset(self.settings, default_preset)
        
        self.albedo_arr: Optional[np.ndarray] = None
        self.generated_maps: Dict[str, np.ndarray] = {}
        self.status: str = "Pendiente"  # "Pendiente", "Generado", "Exportado", "Error"
        self.thumbnail: Optional[Image.Image] = None
        self.dimensions: tuple = (0, 0)

        self.load_albedo()

    def load_albedo(self):
        """Loads image data and creates a small thumbnail."""
        try:
            self.albedo_arr = PBREngine.load_image(self.file_path)
            h, w = self.albedo_arr.shape[:2]
            self.dimensions = (w, h)
            
            # Create fast thumbnail (64x64)
            pil_img = PBREngine.numpy_to_image(self.albedo_arr)
            pil_img.thumbnail((64, 64), Image.Resampling.LANCZOS)
            self.thumbnail = pil_img
        except Exception as e:
            self.status = f"Error: {str(e)}"

    def apply_preset(self, preset_name: str):
        self.preset_name = preset_name
        PresetManager.apply_preset(self.settings, preset_name)

    def generate_maps(self) -> bool:
        """Generates all PBR maps for this item."""
        if self.albedo_arr is None:
            return False
        try:
            self.generated_maps = PBREngine.generate_all_maps(self.albedo_arr, self.settings)
            self.status = "Generado"
            return True
        except Exception as e:
            self.status = f"Error: {str(e)}"
            return False

    def export_to_project(self, project: ProjectTarget, base_export_config: Optional[ExportConfig] = None) -> Dict[str, str]:
        """Exports this material's maps directly into the project target directory."""
        if not self.generated_maps:
            self.generate_maps()

        # Adjust settings for target engine if needed
        if project.normal_directx != self.settings.normal_flip_y:
            self.settings.normal_flip_y = project.normal_directx
            # Recompute normal and orm
            self.generated_maps["normal"] = PBREngine.generate_normal_map(
                self.generated_maps["height"], self.albedo_arr, self.settings
            )
            self.generated_maps["orm"] = PBREngine.generate_orm_packed(
                self.generated_maps["ao"], self.generated_maps["roughness"], self.generated_maps["metallic"]
            )

        # Output directory
        if project.subfolder_per_material:
            out_dir = os.path.join(project.destination_path, self.name)
        else:
            out_dir = project.destination_path

        os.makedirs(out_dir, exist_ok=True)

        config = ExportConfig()
        if base_export_config:
            config.suffixes = base_export_config.suffixes.copy()
            config.enabled_maps = base_export_config.enabled_maps.copy()
        
        config.output_directory = out_dir
        config.base_name = self.name
        config.format = project.format
        config.enabled_maps["orm"] = project.pack_orm

        saved = PBRExporter.export_all_maps(self.generated_maps, config)
        self.status = "Exportado"
        return saved


class BatchManager:
    """Manages the full list of queued materials."""
    def __init__(self):
        self.items: List[BatchMaterialItem] = []

    def add_files(self, file_paths: List[str], default_preset: str = "Piedra / Roca (Stone / Rock)") -> List[BatchMaterialItem]:
        added = []
        valid_exts = {".png", ".jpg", ".jpeg", ".tga", ".bmp", ".tif", ".tiff", ".webp", ".avif"}
        existing_paths = {item.file_path for item in self.items}

        for path in file_paths:
            ext = os.path.splitext(path)[1].lower()
            if ext in valid_exts and path not in existing_paths and os.path.exists(path):
                item = BatchMaterialItem(path, default_preset=default_preset)
                self.items.append(item)
                added.append(item)
        return added

    def remove_item(self, item_id: str):
        self.items = [item for item in self.items if item.id != item_id]

    def clear(self):
        self.items.clear()

    def get_item(self, item_id: str) -> Optional[BatchMaterialItem]:
        for item in self.items:
            if item.id == item_id:
                return item
        return None

    def process_all(self, progress_callback: Optional[Callable[[int, int, str], None]] = None):
        """Processes and generates PBR maps for all items in queue."""
        total = len(self.items)
        for i, item in enumerate(self.items):
            if progress_callback:
                progress_callback(i + 1, total, item.name)
            item.generate_maps()

    def export_all_to_project(
        self, 
        project: ProjectTarget, 
        progress_callback: Optional[Callable[[int, int, str], None]] = None
    ) -> int:
        """Exports all items in queue into the selected project destination."""
        total = len(self.items)
        count = 0
        for i, item in enumerate(self.items):
            if progress_callback:
                progress_callback(i + 1, total, item.name)
            item.export_to_project(project)
            count += 1
        return count
