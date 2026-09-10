"""
Project Destination & Target Engine Management
Allows saving, managing, and instantly selecting export destinations for Godot, Blender, Unreal, Unity, and custom game projects.
"""

import os
import json
from typing import List, Dict, Optional, Any


class ProjectTarget:
    """Represents a configured destination project/engine."""
    def __init__(
        self,
        name: str,
        destination_path: str,
        engine_type: str = "Godot 4",
        format: str = "PNG",
        pack_orm: bool = True,
        normal_directx: bool = False,
        subfolder_per_material: bool = True,
        is_default: bool = False
    ):
        self.name: str = name
        self.destination_path: str = destination_path
        self.engine_type: str = engine_type  # "Godot 4", "Blender", "Unreal Engine 5", "Unity", "Custom"
        self.format: str = format            # "PNG", "TGA", "JPEG", "TIFF"
        self.pack_orm: bool = pack_orm
        self.normal_directx: bool = normal_directx  # True = DirectX (UE), False = OpenGL (Blender/Godot/Unity)
        self.subfolder_per_material: bool = subfolder_per_material
        self.is_default: bool = is_default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "destination_path": self.destination_path,
            "engine_type": self.engine_type,
            "format": self.format,
            "pack_orm": self.pack_orm,
            "normal_directx": self.normal_directx,
            "subfolder_per_material": self.subfolder_per_material,
            "is_default": self.is_default,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectTarget":
        return cls(
            name=data.get("name", "Nuevo Proyecto"),
            destination_path=data.get("destination_path", ""),
            engine_type=data.get("engine_type", "Godot 4"),
            format=data.get("format", "PNG"),
            pack_orm=data.get("pack_orm", True),
            normal_directx=data.get("normal_directx", False),
            subfolder_per_material=data.get("subfolder_per_material", True),
            is_default=data.get("is_default", False)
        )


class ProjectManager:
    """Manages saved project destinations and persistent storage."""

    @staticmethod
    def get_config_path() -> str:
        try:
            home = os.path.expanduser("~")
            config_dir = os.path.join(home, ".pbr_studio")
            os.makedirs(config_dir, exist_ok=True)
            return os.path.join(config_dir, "projects.json")
        except Exception:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            return os.path.join(base_dir, ".pbr_projects.json")

    @classmethod
    def load_projects(cls) -> List[ProjectTarget]:
        config_path = cls.get_config_path()
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                projects = [ProjectTarget.from_dict(item) for item in data]
                if projects:
                    return projects
            except Exception:
                pass

        # Default starter projects if none saved yet
        desktop_dir = os.path.expanduser("~/Desktop")
        defaults = [
            ProjectTarget(
                name="Godot 4 - Assets/Materials",
                destination_path=os.path.join(desktop_dir, "Godot_Materials"),
                engine_type="Godot 4",
                format="PNG",
                pack_orm=True,
                normal_directx=False,
                subfolder_per_material=True,
                is_default=True
            ),
            ProjectTarget(
                name="Blender - Assets Library",
                destination_path=os.path.join(desktop_dir, "Blender_Materials"),
                engine_type="Blender",
                format="PNG",
                pack_orm=True,
                normal_directx=False,
                subfolder_per_material=True
            ),
            ProjectTarget(
                name="Unreal Engine 5 - Content/Textures",
                destination_path=os.path.join(desktop_dir, "Unreal_Materials"),
                engine_type="Unreal Engine 5",
                format="PNG",
                pack_orm=True,
                normal_directx=True,  # DirectX Y-
                subfolder_per_material=True
            ),
            ProjectTarget(
                name="Unity - Assets/Textures",
                destination_path=os.path.join(desktop_dir, "Unity_Materials"),
                engine_type="Unity",
                format="PNG",
                pack_orm=True,
                normal_directx=False,
                subfolder_per_material=True
            )
        ]
        cls.save_projects(defaults)
        return defaults

    @classmethod
    def save_projects(cls, projects: List[ProjectTarget]):
        try:
            config_path = cls.get_config_path()
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            data = [p.to_dict() for p in projects]
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
        except Exception:
            try:
                base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                fallback_path = os.path.join(base_dir, ".pbr_projects.json")
                data = [p.to_dict() for p in projects]
                with open(fallback_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
            except Exception as e:
                print(f"Error saving projects: {e}")
