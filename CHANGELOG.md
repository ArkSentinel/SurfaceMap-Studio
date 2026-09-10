# Registro de Cambios (Changelog)

Todas las modificaciones notables de este proyecto estan documentadas en este archivo.
El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.0.0/) y se adhiere a [Semantic Versioning](https://semver.org/lang/es/).

---

## [1.2.0] - 2026-09-10

### Anadido
- **Nombre Oficial del Proyecto**: `SurfaceMap Studio`.
- **Soporte Completo para Formato AVIF**:
  - Lectura, procesamiento y generacion de mapas PBR a partir de texturas `.avif`.
  - Exportacion individual y por lotes en formato `.avif` de alta compresion moderna.
- **Gestion de Proyectos y Destinos Directos**:
  - Configuracion persistente de carpetas destino para Godot 4, Blender, Unreal Engine 5, Unity y carpetas personalizadas.
  - Boton de exportacion directa en 1 clic (`Exportar al Proyecto` / `Ctrl+S`).
  - Dialogo modal para crear, editar, duplicar y eliminar proyectos guardados.
- **Procesamiento por Lotes (Multi-Texture Batch Queue)**:
  - Cola lateral con miniaturas de texturas, resolucion y estado en tiempo real.
  - Asignacion de presets individuales por textura o aplicacion masiva con `Preset Global`.
  - Boton para procesar y exportar todo el lote con barra de progreso.
- **Flujos CI/CD automatizados**:
  - Workflow de GitHub Actions para pruebas continuas en Ubuntu, macOS y Windows.
  - Workflow automatizado de creacion de binarios ejecutables para releases.

### Modificado
- Limpieza integral de iconos tipograficos y emojis en la interfaz grafica y documentacion para garantizar un diseno sobrio de nivel industrial.
- Optimizacion del procesamiento vectorizado y el viewport de vista previa.

---

## [1.1.0] - 2026-09-10

### Anadido
- **Presets Especializados**:
  - RTS / Estrategia: Terrenos de alta legibilidad, Fachadas de edificios y Vegetacion.
  - Animacion y Estilizado: Cartoon con biselado suave, Hand-Painted / Arcane y Anime Cel-Shading.
  - Sci-Fi / Hard-Surface: Paneles de naves y Armaduras mecha.
  - Retro 3D / Low-Poly.

---

## [1.0.0] - 2026-09-10

### Anadido
- Lanzamiento inicial de **SurfaceMap Studio**.
- Motor de generacion de mapas PBR: Normal, Height, Roughness, Metallic, Ambient Occlusion, Specular y ORM Packed.
- Visor 2D interactivo con zoom, paneo y modo de comparacion en pantalla dividida (Split View).
- Visor 3D en tiempo real con renderizado de esfera PBR basado en Cook-Torrance GGX y controles orbitales.
- Panel de personalizacion de parametros en tiempo real con respuesta instantanea.
- Exportador multiformato (PNG, TGA, AVIF, JPEG, TIFF) y escalado de resolucion.
- Soporte multiplataforma para macOS, Windows y Linux.
