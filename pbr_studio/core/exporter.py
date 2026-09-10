"""
PBR Texture Exporter
Exports generated PBR maps to disk with customizable formats, resolutions, and naming conventions.
"""

import os
from typing import Dict, Optional, Tuple
import numpy as np
from PIL import Image
from .pbr_engine import PBREngine


class ExportConfig:
    """Export configuration settings."""
    def __init__(self):
        self.output_directory: str = ""
        self.base_name: str = "material"
        self.format: str = "PNG"  # "PNG", "JPEG", "TGA", "TIFF"
        self.jpeg_quality: int = 95
        self.resolution: Optional[Tuple[int, int]] = None  # None = original, or (1024, 1024), etc.
        
        # Suffix configurations
        self.suffixes: Dict[str, str] = {
            "albedo": "_albedo",
            "normal": "_normal",
            "height": "_height",
            "roughness": "_roughness",
            "metallic": "_metallic",
            "ao": "_ao",
            "specular": "_specular",
            "orm": "_orm"
        }
        
        # Selection of maps to export
        self.enabled_maps: Dict[str, bool] = {
            "albedo": True,
            "normal": True,
            "height": True,
            "roughness": True,
            "metallic": True,
            "ao": True,
            "specular": False,
            "orm": True
        }


class PBRExporter:
    """Handles saving PBR map arrays to images on disk."""

    @staticmethod
    def export_single_map(
        map_name: str,
        map_array: np.ndarray,
        config: ExportConfig,
        custom_filepath: Optional[str] = None
    ) -> str:
        """Exports a single map array to disk. Returns the saved filepath."""
        if custom_filepath:
            save_path = custom_filepath
        else:
            suffix = config.suffixes.get(map_name, f"_{map_name}")
            ext = config.format.lower()
            if ext == "jpeg":
                ext = "jpg"
            filename = f"{config.base_name}{suffix}.{ext}"
            save_path = os.path.join(config.output_directory, filename)

        os.makedirs(os.path.dirname(os.path.abspath(save_path)), exist_ok=True)
        img = PBREngine.numpy_to_image(map_array)

        # Handle resolution scaling
        if config.resolution and config.resolution != img.size:
            img = img.resize(config.resolution, Image.Resampling.LANCZOS)

        # Save based on format
        fmt = config.format.upper()
        if fmt == "JPEG" or fmt == "JPG":
            if img.mode != "RGB":
                img = img.convert("RGB")
            img.save(save_path, format="JPEG", quality=config.jpeg_quality)
        elif fmt == "PNG":
            img.save(save_path, format="PNG", optimize=True)
        elif fmt == "TGA":
            img.save(save_path, format="TGA")
        elif fmt == "AVIF":
            if img.mode not in ("RGB", "RGBA"):
                img = img.convert("RGB")
            img.save(save_path, format="AVIF")
        elif fmt == "TIFF":
            img.save(save_path, format="TIFF")
        else:
            img.save(save_path)

        return save_path

    @staticmethod
    def export_all_maps(
        maps_dict: Dict[str, np.ndarray],
        config: ExportConfig
    ) -> Dict[str, str]:
        """
        Exports all enabled maps in maps_dict.
        Returns a dictionary mapping map_name -> saved_filepath.
        """
        saved_files = {}
        for map_name, map_array in maps_dict.items():
            if config.enabled_maps.get(map_name, True):
                saved_path = PBRExporter.export_single_map(map_name, map_array, config)
                saved_files[map_name] = saved_path
        return saved_files
