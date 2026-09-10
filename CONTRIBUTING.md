# Guia de Contribucion

Gracias por tu interes en contribuir a **SurfaceMap Studio**.

---

## Como Contribuir

1. **Haz un Fork** del repositorio en GitHub.
2. **Crea una Rama** para tu funcionalidad o correccion:
   ```bash
   git checkout -b feature/nueva-funcionalidad
   ```
3. **Configura el Entorno de Desarrollo**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```
4. **Ejecuta los Tests Unitarios**:
   ```bash
   python3 -m unittest discover -s tests
   ```
5. **Realiza tus Cambios** manteniendo los siguientes principios:
   - Evitar el uso de emojis en interfaces de usuario, codigo y documentacion oficial.
   - Mantener compatibilidad multiplataforma (macOS, Windows, Linux).
   - Asegurar que todas las operaciones matematicas en `pbr_engine.py` esten vectorizadas con NumPy para mantener un alto rendimiento.
6. **Envia un Pull Request** con una descripcion clara de las mejoras introducidas.
