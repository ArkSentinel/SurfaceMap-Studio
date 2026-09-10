from setuptools import setup, find_packages

setup(
    name="surfacemap-studio",
    version="1.2.1",
    packages=find_packages(),
    install_requires=[
        "PyQt6>=6.5.0",
        "numpy>=1.24.0",
        "Pillow>=9.5.0",
        "scipy>=1.10.0",
    ],
    entry_points={
        "console_scripts": [
            "surfacemap-studio=pbr_studio.app:main",
            "surfacemap=pbr_studio.app:main",
        ],
    },
)
