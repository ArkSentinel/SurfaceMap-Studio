"""
PBR Generation Engine
Fast, vectorized mathematical algorithms to generate complete PBR texture sets
(Normal, Height, Roughness, Metallic, Ambient Occlusion, Specular, ORM/ARM Packed).
"""

from typing import Dict, Tuple, Optional
import numpy as np
from PIL import Image, ImageFilter, ImageOps


class PBRMapSettings:
    """Configuration container for all PBR map generation parameters."""
    def __init__(self):
        # Height map settings
        self.height_contrast: float = 1.2
        self.height_brightness: float = 0.0
        self.height_blur: float = 1.0
        self.height_invert: bool = False
        self.height_source: str = "luminance"  # "luminance", "red", "green", "blue", "max_rgb", "min_rgb"

        # Normal map settings
        self.normal_strength: float = 2.5
        self.normal_filter: str = "scharr"     # "sobel", "scharr", "simple"
        self.normal_flip_y: bool = False       # True = DirectX (Y-), False = OpenGL (Y+)
        self.normal_flip_x: bool = False
        self.normal_detail: float = 0.4        # High frequency detail boost
        self.normal_blur: float = 0.0

        # Roughness map settings
        self.roughness_base: float = 0.55
        self.roughness_contrast: float = 1.1
        self.roughness_invert: bool = False    # True = Glossiness/Smoothness
        self.roughness_min: float = 0.05
        self.roughness_max: float = 0.95
        self.roughness_high_freq: float = 0.3  # Micro-roughness variance

        # Metallic map settings
        self.metallic_mode: str = "auto"       # "auto", "threshold", "manual_constant"
        self.metallic_threshold: float = 0.65
        self.metallic_tolerance: float = 0.25
        self.metallic_base_val: float = 0.0
        self.metallic_invert: bool = False

        # AO map settings
        self.ao_intensity: float = 1.5
        self.ao_radius: int = 8
        self.ao_spread: float = 1.2
        self.ao_contrast: float = 1.3
        self.ao_invert: bool = False

        # Specular map settings
        self.specular_dielectric_f0: float = 0.04  # Standard default ~0.04 (4% reflectance)

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    def from_dict(self, data: dict):
        for k, v in data.items():
            if hasattr(self, k):
                setattr(self, k, v)


class PBREngine:
    """High-performance PBR map generator using NumPy and PIL."""

    @staticmethod
    def load_image(file_path: str) -> np.ndarray:
        """Loads an image and returns an RGB float32 numpy array [0.0, 1.0]."""
        with Image.open(file_path) as img:
            img = img.convert("RGB")
            arr = np.array(img, dtype=np.float32) / 255.0
        return arr

    @staticmethod
    def numpy_to_image(arr: np.ndarray) -> Image.Image:
        """Converts float32 numpy array [0.0, 1.0] to PIL Image (RGB or L)."""
        clamped = np.clip(arr, 0.0, 1.0)
        uint8_arr = (clamped * 255.0).astype(np.uint8)
        if uint8_arr.ndim == 2:
            return Image.fromarray(uint8_arr)
        elif uint8_arr.ndim == 3:
            return Image.fromarray(uint8_arr)
        raise ValueError(f"Unsupported array shape for image conversion: {arr.shape}")

    @staticmethod
    def image_to_numpy(img: Image.Image) -> np.ndarray:
        """Converts PIL Image to float32 numpy array [0.0, 1.0]."""
        return np.array(img, dtype=np.float32) / 255.0

    @classmethod
    def generate_height_map(cls, albedo: np.ndarray, settings: PBRMapSettings) -> np.ndarray:
        """
        Generates a grayscale Height/Displacement map from the base color.
        Uses perceptual luminance with contrast curves, brightness offset, and optional blur.
        """
        if albedo.ndim == 3:
            if settings.height_source == "luminance":
                # ITU-R BT.709 perceptual luma
                height = 0.2126 * albedo[:, :, 0] + 0.7152 * albedo[:, :, 1] + 0.0722 * albedo[:, :, 2]
            elif settings.height_source == "red":
                height = albedo[:, :, 0]
            elif settings.height_source == "green":
                height = albedo[:, :, 1]
            elif settings.height_source == "blue":
                height = albedo[:, :, 2]
            elif settings.height_source == "max_rgb":
                height = np.max(albedo, axis=2)
            elif settings.height_source == "min_rgb":
                height = np.min(albedo, axis=2)
            else:
                height = 0.299 * albedo[:, :, 0] + 0.587 * albedo[:, :, 1] + 0.114 * albedo[:, :, 2]
        else:
            height = albedo.copy()

        # Apply brightness and contrast: centered around 0.5
        height = (height - 0.5) * settings.height_contrast + 0.5 + settings.height_brightness

        if settings.height_invert:
            height = 1.0 - height

        height = np.clip(height, 0.0, 1.0)

        # Optional Gaussian smoothing
        if settings.height_blur > 0.05:
            pil_img = cls.numpy_to_image(height)
            pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=settings.height_blur))
            height = cls.image_to_numpy(pil_img)

        return np.clip(height, 0.0, 1.0)

    @classmethod
    def generate_normal_map(
        cls, 
        height: np.ndarray, 
        albedo: Optional[np.ndarray], 
        settings: PBRMapSettings
    ) -> np.ndarray:
        """
        Generates an RGB Normal map from height map using Sobel/Scharr derivative convolution.
        Output is encoded as RGB in [0.0, 1.0] representing normal vectors [-1..1, -1..1, 0..1].
        """
        h, w = height.shape[:2]
        
        # Convolution kernels for dX and dY
        if settings.normal_filter == "scharr":
            kx = np.array([[-3, 0, 3],
                           [-10, 0, 10],
                           [-3, 0, 3]], dtype=np.float32) / 32.0
            ky = np.array([[-3, -10, -3],
                           [0,    0,  0],
                           [3,   10,  3]], dtype=np.float32) / 32.0
        elif settings.normal_filter == "simple":
            kx = np.array([[0, 0, 0],
                           [-1, 0, 1],
                           [0, 0, 0]], dtype=np.float32) / 2.0
            ky = np.array([[0, -1, 0],
                           [0,  0, 0],
                           [0,  1, 0]], dtype=np.float32) / 2.0
        else:  # Sobel
            kx = np.array([[-1, 0, 1],
                           [-2, 0, 2],
                           [-1, 0, 1]], dtype=np.float32) / 8.0
            ky = np.array([[-1, -2, -1],
                           [0,   0,  0],
                           [1,   2,  1]], dtype=np.float32) / 8.0

        # Vectorized 2D convolution with edge padding
        padded = np.pad(height, pad_width=1, mode='edge')
        
        # Calculate gradients using slicing (fastest numpy method)
        dx = (
            kx[0, 0] * padded[:-2, :-2] + kx[0, 1] * padded[:-2, 1:-1] + kx[0, 2] * padded[:-2, 2:] +
            kx[1, 0] * padded[1:-1, :-2] + kx[1, 1] * padded[1:-1, 1:-1] + kx[1, 2] * padded[1:-1, 2:] +
            kx[2, 0] * padded[2:, :-2]   + kx[2, 1] * padded[2:, 1:-1]   + kx[2, 2] * padded[2:, 2:]
        )
        dy = (
            ky[0, 0] * padded[:-2, :-2] + ky[0, 1] * padded[:-2, 1:-1] + ky[0, 2] * padded[:-2, 2:] +
            ky[1, 0] * padded[1:-1, :-2] + ky[1, 1] * padded[1:-1, 1:-1] + ky[1, 2] * padded[1:-1, 2:] +
            ky[2, 0] * padded[2:, :-2]   + ky[2, 1] * padded[2:, 1:-1]   + ky[2, 2] * padded[2:, 2:]
        )

        # High-frequency detail overlay (from high-pass on albedo)
        if settings.normal_detail > 0.01 and albedo is not None:
            gray = 0.299 * albedo[:, :, 0] + 0.587 * albedo[:, :, 1] + 0.114 * albedo[:, :, 2]
            gray_pil = cls.numpy_to_image(gray)
            blurred = cls.image_to_numpy(gray_pil.filter(ImageFilter.GaussianBlur(radius=2.0)))
            high_freq = gray - blurred
            
            # Simple high freq gradients
            hf_pad = np.pad(high_freq, pad_width=1, mode='edge')
            h_dx = (hf_pad[1:-1, 2:] - hf_pad[1:-1, :-2]) * 0.5
            h_dy = (hf_pad[2:, 1:-1] - hf_pad[:-2, 1:-1]) * 0.5
            
            dx += h_dx * (settings.normal_detail * 3.0)
            dy += h_dy * (settings.normal_detail * 3.0)

        # Apply normal strength factor
        dx *= settings.normal_strength
        dy *= settings.normal_strength

        # Flip axes if required (DirectX vs OpenGL format)
        if settings.normal_flip_x:
            dx = -dx
        if settings.normal_flip_y:
            dy = -dy  # Inverted Y for DirectX

        # Normal vector: [-dx, -dy, 1.0]
        nx = -dx
        ny = -dy
        nz = np.ones((h, w), dtype=np.float32)

        # Normalize vector length
        length = np.sqrt(nx * nx + ny * ny + nz * nz)
        length[length == 0] = 1.0
        nx /= length
        ny /= length
        nz /= length

        # Pack into RGB [0.0, 1.0]
        normal_rgb = np.zeros((h, w, 3), dtype=np.float32)
        normal_rgb[:, :, 0] = nx * 0.5 + 0.5
        normal_rgb[:, :, 1] = ny * 0.5 + 0.5
        normal_rgb[:, :, 2] = nz * 0.5 + 0.5

        if settings.normal_blur > 0.05:
            pil_img = cls.numpy_to_image(normal_rgb)
            pil_img = pil_img.filter(ImageFilter.GaussianBlur(radius=settings.normal_blur))
            normal_rgb = cls.image_to_numpy(pil_img)

        return np.clip(normal_rgb, 0.0, 1.0)

    @classmethod
    def generate_roughness_map(
        cls, 
        height: np.ndarray, 
        albedo: Optional[np.ndarray], 
        settings: PBRMapSettings
    ) -> np.ndarray:
        """
        Generates Roughness map.
        Roughness correlates with micro-surface variations (high frequency detail + height variation).
        """
        # Base variation from height
        rough = (height - 0.5) * settings.roughness_contrast + 0.5

        # Extract micro-surface high-frequency noise from albedo if available
        if albedo is not None and settings.roughness_high_freq > 0.01:
            gray = 0.299 * albedo[:, :, 0] + 0.587 * albedo[:, :, 1] + 0.114 * albedo[:, :, 2]
            gray_pil = cls.numpy_to_image(gray)
            blurred = cls.image_to_numpy(gray_pil.filter(ImageFilter.GaussianBlur(radius=3.0)))
            high_freq = np.abs(gray - blurred)
            rough = rough * (1.0 - settings.roughness_high_freq) + high_freq * settings.roughness_high_freq * 2.0

        # Offset with base roughness
        rough = rough + (settings.roughness_base - 0.5)

        # Invert if Smoothness / Glossiness workflow
        if settings.roughness_invert:
            rough = 1.0 - rough

        # Remap to min-max bounds
        rough = settings.roughness_min + rough * (settings.roughness_max - settings.roughness_min)

        return np.clip(rough, 0.0, 1.0)

    @classmethod
    def generate_metallic_map(
        cls, 
        albedo: np.ndarray, 
        settings: PBRMapSettings
    ) -> np.ndarray:
        """
        Generates Metallic map.
        Metals usually have high reflectance / brightness and distinct chroma vs non-metals.
        """
        if settings.metallic_mode == "manual_constant":
            h, w = albedo.shape[:2]
            val = settings.metallic_base_val
            if settings.metallic_invert:
                val = 1.0 - val
            return np.full((h, w), val, dtype=np.float32)

        # Luminance & Brightness calculation
        luma = 0.2126 * albedo[:, :, 0] + 0.7152 * albedo[:, :, 1] + 0.0722 * albedo[:, :, 2]
        
        # Color saturation
        max_c = np.max(albedo, axis=2)
        min_c = np.min(albedo, axis=2)
        delta = max_c - min_c
        saturation = np.zeros_like(luma)
        mask = max_c > 0.001
        saturation[mask] = delta[mask] / max_c[mask]

        # Metals typically have high luminance and either low saturation (silver/chrome/iron) or colored tint (gold/copper)
        # We calculate soft threshold around metallic_threshold with tolerance
        t = settings.metallic_threshold
        tol = max(0.01, settings.metallic_tolerance)
        
        metallic = (luma - (t - tol)) / (2.0 * tol)
        metallic = np.clip(metallic, 0.0, 1.0)
        
        # Smooth S-curve
        metallic = metallic * metallic * (3.0 - 2.0 * metallic)

        if settings.metallic_invert:
            metallic = 1.0 - metallic

        return np.clip(metallic, 0.0, 1.0)

    @classmethod
    def generate_ao_map(cls, height: np.ndarray, settings: PBRMapSettings) -> np.ndarray:
        """
        Generates Ambient Occlusion (AO) / Cavity Map.
        Simulates light attenuation in crevices using multi-scale blurred height differences.
        """
        h_pil = cls.numpy_to_image(height)
        
        # Multi-scale occlusion approximation
        r1 = max(1.0, float(settings.ao_radius) * 0.5)
        r2 = max(2.0, float(settings.ao_radius))
        r3 = max(4.0, float(settings.ao_radius) * 2.0)

        b1 = cls.image_to_numpy(h_pil.filter(ImageFilter.GaussianBlur(radius=r1)))
        b2 = cls.image_to_numpy(h_pil.filter(ImageFilter.GaussianBlur(radius=r2)))
        b3 = cls.image_to_numpy(h_pil.filter(ImageFilter.GaussianBlur(radius=r3)))

        # Cavity: height minus surrounding average
        diff1 = np.maximum(0.0, b1 - height)
        diff2 = np.maximum(0.0, b2 - height)
        diff3 = np.maximum(0.0, b3 - height)

        combined_diff = (diff1 * 0.5 + diff2 * 0.35 + diff3 * 0.15) * settings.ao_intensity * 3.0
        ao = 1.0 - combined_diff

        # Contrast adjustment
        ao = (ao - 0.5) * settings.ao_contrast + 0.5
        
        if settings.ao_invert:
            ao = 1.0 - ao

        return np.clip(ao, 0.0, 1.0)

    @classmethod
    def generate_specular_map(
        cls, 
        albedo: np.ndarray, 
        metallic: np.ndarray, 
        settings: PBRMapSettings
    ) -> np.ndarray:
        """
        Generates Specular F0 Map:
        - Dielectrics (metallic ~ 0): ~0.04 grayscale
        - Conductors (metallic ~ 1): Tinted base color
        """
        dielectric_color = np.full_like(albedo, settings.specular_dielectric_f0)
        metallic_3d = np.repeat(metallic[:, :, np.newaxis], 3, axis=2)
        specular = dielectric_color * (1.0 - metallic_3d) + albedo * metallic_3d
        return np.clip(specular, 0.0, 1.0)

    @classmethod
    def generate_orm_packed(
        cls, 
        ao: np.ndarray, 
        roughness: np.ndarray, 
        metallic: np.ndarray
    ) -> np.ndarray:
        """
        Packs AO, Roughness, and Metallic into an RGB texture (R=AO, G=Roughness, B=Metallic).
        Standard packed format for Unreal Engine, Godot, Blender glTF.
        """
        h, w = ao.shape[:2]
        orm = np.zeros((h, w, 3), dtype=np.float32)
        orm[:, :, 0] = ao
        orm[:, :, 1] = roughness
        orm[:, :, 2] = metallic
        return np.clip(orm, 0.0, 1.0)

    @classmethod
    def generate_all_maps(
        cls, 
        albedo: np.ndarray, 
        settings: PBRMapSettings
    ) -> Dict[str, np.ndarray]:
        """Generates all PBR maps in one pass."""
        height = cls.generate_height_map(albedo, settings)
        normal = cls.generate_normal_map(height, albedo, settings)
        roughness = cls.generate_roughness_map(height, albedo, settings)
        metallic = cls.generate_metallic_map(albedo, settings)
        ao = cls.generate_ao_map(height, settings)
        specular = cls.generate_specular_map(albedo, metallic, settings)
        orm = cls.generate_orm_packed(ao, roughness, metallic)

        return {
            "albedo": albedo,
            "normal": normal,
            "height": height,
            "roughness": roughness,
            "metallic": metallic,
            "ao": ao,
            "specular": specular,
            "orm": orm,
        }
