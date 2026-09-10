# SurfaceMap Studio

Aplicacion de escritorio profesional, rapida y multiplataforma (**macOS, Windows, Linux**) desarrollada en **Python** con **PyQt6** y **NumPy** para convertir y sintetizar texturas base (Albedo / Difusa o Mapa de Altura) en sets completos de materiales de superficie fisica **PBR (Physically Based Rendering)** con ajuste y previsualizacion en tiempo real, gestion de proyectos (Godot, Blender, Unreal, Unity) y procesamiento por lotes.

Repositorio oficial: [https://github.com/ArkSentinel/SurfaceMap-Studio](https://github.com/ArkSentinel/SurfaceMap-Studio)

---

## Descargas y Paquetes de Instalacion (Releases)

Puedes descargar los paquetes precompilados listos para usar directamente desde la seccion de [Releases de GitHub](https://github.com/ArkSentinel/SurfaceMap-Studio/releases):

| Plataforma / Distribucion | Formato de Paquete | Descripcion |
|---|---|---|
| **Ubuntu / Debian / Mint / Pop!_OS** | `.deb` (`surfacemap-studio_1.2.0_amd64.deb`) | Instalador nativo Debian/Ubuntu |
| **Fedora / RHEL / openSUSE** | `.rpm` (`surfacemap-studio-1.2.0-1.x86_64.rpm`) | Paquete RPM nativo |
| **Arch Linux / Manjaro** | `PKGBUILD` (`surfacemap-studio-arch-PKGBUILD.tar.gz`) | Construccion e instalacion con `makepkg` |
| **Linux (Universal Portable)** | `.tar.gz` (`surfacemap-studio-linux-x86_64.tar.gz`) | Ejecutable independiente sin instalacion |
| **Windows 10 / 11 (64-bit)** | `.zip` (`surfacemap-studio-windows-x86_64.zip`) | Binario ejecutable portatil (`.exe`) |
| **macOS (Apple Silicon & Intel)** | `.zip` (`surfacemap-studio-macos-universal.zip`) | Bundle de aplicacion macOS (`.app`) |

---

## Instrucciones de Instalacion por Sistema Operativo

### 1. Ubuntu, Debian, Linux Mint, Pop!_OS (.deb)
Descarga el archivo `.deb` desde Releases e instalalo mediante terminal:
```bash
sudo apt update
sudo apt install ./surfacemap-studio_1.2.0_amd64.deb
```
O ejecutalo directamente desde el lanzador de aplicaciones de tu entorno de escritorio.

### 2. Fedora, RHEL, openSUSE (.rpm)
```bash
sudo dnf install ./surfacemap-studio-1.2.0-1.x86_64.rpm
```
*(En openSUSE: `sudo zypper install ./surfacemap-studio-1.2.0-1.x86_64.rpm`)*

### 3. Arch Linux, Manjaro (PKGBUILD)
```bash
tar -xzvf surfacemap-studio-arch-PKGBUILD.tar.gz
cd packaging/arch  # o la carpeta extraida
makepkg -si
```

### 4. Windows
1. Descarga `surfacemap-studio-windows-x86_64.zip`.
2. Descomprime la carpeta en la ubicacion que prefieras.
3. Haz doble clic en `surfacemap-studio.exe`.

### 5. macOS
1. Descarga `surfacemap-studio-macos-universal.zip`.
2. Descomprime el archivo y arrastra `SurfaceMap Studio.app` a tu carpeta `Aplicaciones`.

---

## Ejecucion desde Codigo Fuente

### Requisitos
- Python 3.9 o superior.

### En macOS / Linux
```bash
git clone https://github.com/ArkSentinel/SurfaceMap-Studio.git
cd SurfaceMap-Studio

chmod +x run.sh
./run.sh
```

### En Windows
```cmd
git clone https://github.com/ArkSentinel/SurfaceMap-Studio.git
cd SurfaceMap-Studio
run.bat
```

---

## Caracteristicas Principales

### 1. Gestion de Destinos de Proyectos (Godot, Blender, Unreal, Unity)
- **Destinos Persistentes**: Define las carpetas de tus proyectos una sola vez y exporta directamente sin necesidad de seleccionar la ruta en cada operacion.
- **Perfiles Preconfigurados por Motor**:
  - **Godot 4**: Empaquetado ORM (**R** = AO, **G** = Roughness, **B** = Metallic), Normales OpenGL ($Y^+$), formato PNG/AVIF.
  - **Blender**: Set completo de mapas PBR independientes y empaquetado ORM, Normales OpenGL ($Y^+$), formato PNG.
  - **Unreal Engine 5**: Normales DirectX ($Y^-$ / canal verde invertido), empaquetado ORM, formatos PNG/TGA.
  - **Unity**: Normales OpenGL, soporte para inversion de rugosidad a suavidad (*Smoothness*).
  - **Personalizado**: Control total de subcarpetas, nombres, extensiones y compresion.
- **Exportacion Instantanea**: Boton `Exportar al Proyecto` (`Ctrl+S`) en la barra principal para guardar el material activo directamente en la carpeta del proyecto seleccionado.

### 2. Procesamiento por Lotes (Multi-Texture Batch Queue)
- **Carga Masiva**: Arrastra y suelta 1 o 50 imagenes a la vez a la ventana o al panel lateral.
- **Cola de Materiales con Miniaturas**: Visualizacion de miniaturas generadas al vuelo, resolucion de cada imagen y estado del proceso.
- **Ajustes Individuales**: Haz clic en cualquier textura de la cola para calibrar sus parametros y previsualizarla en los visores 2D y 3D en tiempo real.
- **Presets Globales o Individuales**: Asigna un preset especifico a cada textura o utiliza el selector `Preset Global...` para aplicarlo a todas las texturas de la cola simultaneamente.
- **Exportacion Masiva**: Boton `Exportar Todo el Lote al Proyecto` para procesar y exportar toda la cola con indicador de progreso.

### 3. Motor de Generacion PBR Vectorizado
- **Normal Map**: Algoritmos de convolucion Scharr y Sobel, control de fuerza/relieve, selector DirectX ($Y^-$) vs OpenGL ($Y^+$) y realce de micro-detalle por paso alto.
- **Height / Displacement Map**: Luminancia perceptual ITU-R BT.709 o extraccion por canales individuales (R, G, B, Max, Min), contraste, compensacion de brillo y suavizado Gaussiano.
- **Roughness Map**: Analisis de frecuencia superficial, nivel base, contraste, limites (*clamping*) y conmutador a *Smoothness / Glossiness*.
- **Metallic Map**: Modos automatico (deteccion cromatica/luminancia), constante manual y umbral de aislamiento con tolerancia ajustable.
- **Ambient Occlusion (AO) / Cavidad**: Oclusion ambiental multi-escala calculada directamente sobre el relieve de profundidad.
- **Specular Map**: Reflectancia dielectrica F0 calibrada con tintado metalico de conservacion de energia.
- **ORM / ARM Packed Map**: Empaquetado optimizado en un solo archivo RGB (**R** = AO, **G** = Roughness, **B** = Metallic).
- **Formatos Soportados**: Lectura y exportacion en **PNG**, **AVIF**, **TGA**, **JPEG**, **TIFF**, **WEBP** y **BMP**.

### 4. Visualizacion Interactiva en Tiempo Real
- **Visor 2D Avanzado**: Zoom suave centrado en la posicion del cursor del raton, paneo arrastrable y modo **Split Comparison** con cortina interactiva deslizable para comparar la imagen original contra cualquier mapa generado.
- **Visor 3D PBR**: Esfera 3D iluminada en tiempo real mediante el modelo de sombreado fisico Cook-Torrance GGX, con rotacion orbital manual y modo tornamesa (*turntable*) automatico.

### 5. Coleccion de Presets de Materiales
- **RTS y Estrategia**: Terreno / Mapa Aereo (optimizada para reducir aliasing a distancia), Edificios y Murallas, Vegetacion y Bosque.
- **Animacion y Estilizado**: Cartoon (biselado suave sin grano), Hand-Painted / Arcane (pictorico), Anime Cel-Shading.
- **Sci-Fi y Hard-Surface**: Paneles de Nave / Hull, Armadura Mech / Polimero.
- **Retro 3D**: Low-Poly / Pixel 3D (aristas cortantes, acabado mate).
- **Realistas**: Piedra/Roca, Madera Rustica, Madera Pulida, Metal Pulido, Metal Oxidado, Concreto, Baldosas/Ceramica, Tela, Cuero, Plastico/Caucho.

---

## Atajos de Teclado

| Atajo | Accion |
|---|---|
| `Ctrl+O` / `Cmd+O` | Abrir textura individual |
| `Ctrl+Shift+O` / `Cmd+Shift+O` | Cargar lote de texturas |
| `Ctrl+S` / `Cmd+S` | Exportar material al proyecto activo |
| `Ctrl+E` / `Cmd+E` | Abrir dialogo de exportacion personalizada |
| `Ctrl+P` / `Cmd+P` | Gestionar destinos de proyectos |
| `Ctrl+F` / `Cmd+F` | Ajustar visor 2D a la ventana |
| `Ctrl+1` / `Cmd+1` | Zoom 1:1 en visor 2D |
| `Ctrl+Q` / `Cmd+Q` | Salir de la aplicacion |

---

## Estructura del Proyecto

```
SurfaceMap-Studio/
├── .github/
│   └── workflows/
│       ├── ci.yml              # CI multiplataforma (Ubuntu, macOS, Windows)
│       └── release.yml         # Construccion automatizada de .deb, .rpm, Arch, Win, Mac
├── packaging/
│   ├── deb/                    # Herramientas de empaquetado .deb (Ubuntu/Debian)
│   ├── rpm/                    # Especificaciones .rpm (Fedora/RHEL)
│   ├── arch/                   # PKGBUILD para Arch Linux / Manjaro
│   ├── linux/                  # Archivo .desktop para entornos graficos Linux
│   ├── windows/                # Script de instalador para Windows
│   └── macos/                  # Script de empaquetado para macOS
├── pbr_studio/
│   ├── core/
│   │   ├── pbr_engine.py       # Algoritmos matematicos PBR vectorizados
│   │   ├── presets.py          # Definicion y persistencia de presets
│   │   ├── projects.py         # Gestor de destinos y motores (Godot, Blender, UE, Unity)
│   │   ├── batch_manager.py    # Procesador de cola por lotes
│   │   └── exporter.py         # Motor de exportacion multiformato
│   ├── ui/
│   │   ├── main_window.py      # Ventana principal y coordinacion
│   │   ├── preview_2d.py       # Visor 2D interactivo y comparador split
│   │   ├── preview_3d.py       # Visor 3D en tiempo real (Cook-Torrance GGX)
│   │   ├── settings_panel.py   # Panel de control de parametros
│   │   ├── batch_queue_widget.py # Widget de cola de lote
│   │   ├── project_dialog.py   # Dialogo de gestion de proyectos
│   │   ├── export_dialog.py    # Dialogo de exportacion avanzada
│   │   ├── widgets.py          # Sliders y componentes reutilizables
│   │   └── theme.py            # Tema oscuro profesional
│   └── app.py                  # Punto de entrada de la aplicacion
├── samples/                    # Texturas de muestra
├── tests/                      # Suite de tests unitarios
├── CHANGELOG.md                # Registro de versiones y cambios
├── CONTRIBUTING.md             # Guia de contribucion
├── LICENSE                     # Licencia MIT
├── pyproject.toml              # Configuracion estandar de empaquetado
├── requirements.txt            # Dependencias del proyecto
├── run.sh                      # Lanzador para macOS/Linux
├── run.bat                     # Lanzador para Windows
└── main.py                     # Script de inicio
```

---

## Licencia

Este proyecto esta bajo la Licencia MIT. Consulta el archivo [LICENSE](LICENSE) para mas detalles.
