# Dataset Version Control

Una utilidad ligera de control de versiones para conjuntos de datos (datasets) de aprendizaje automático, orientada a garantizar la reproducibilidad científica en pipelines de MLOps. Este módulo funciona de manera análoga a Git, guardando instantáneas (snapshots) físicas comprimidas e indexadas por hashes criptográficos, lo que permite auditar cambios de datos, retornar a versiones anteriores (checkout) y calcular diferencias lógicas de registros.

## Arquitectura y Flujo de Versionado de Datos

El motor de control de versiones gestiona un almacén estructurado oculto en la carpeta `.dvc_store/`:

1.  **Instantáneas de Contenido (Objects Storage):**
    *   Al confirmar un archivo de datos (JSON/CSV), el sistema calcula su firma MD5. El contenido se copia al almacén `.dvc_store/objects/[hash].dat`, evitando duplicaciones físicas de datos redundantes (deduplicación por contenido).
2.  **Historial de Cambios (Commits Log):**
    *   Cada confirmación (commit) genera una clave criptográfica única SHA-1 basada en su mensaje de cambios, marca de tiempo, hash del archivo y el hash del commit padre (parent_hash), permitiendo reconstruir la secuencia de versiones como un Grafo Dirigido Acíclico (DAG).
3.  **Diferenciador Semántico (Data Diffs):**
    *   A diferencia de Git (que calcula diferencias a nivel de líneas de texto plano), este módulo analiza los archivos estructurados JSON extrayendo registros por su llave primaria lógica (`id`, `guid`, o `instruction`).
    *   Compara los registros calculando de manera exacta cuántos objetos han sido agregados, eliminados o modificados en sus atributos internos entre dos versiones dadas.
4.  **Restauración de Trabajo (Checkout):**
    *   Permite restaurar el dataset original en disco copiando de vuelta el snapshot guardado en objetos, reubicando el puntero local HEAD de trabajo.

## Requisitos e Instalacion

*   Python 3.8 o superior
*   Pydantic

Para instalar las dependencias locales, ejecute:

```bash
pip install -r requirements.txt
```

## Pruebas y Verificacion

1.  **Ejecutar Pruebas Unitarias de Historial y Checkout:**
    ```bash
    python -m unittest test_dvc.py
    ```
2.  **Ejecutar Demostración de Historial:**
    ```bash
    python example.py
    ```
    El script creará un dataset v1 de 3 instrucciones, lo confirmará, aplicará mutaciones de registros (agregando, eliminando y modificando), confirmará la versión v2, y mostrará el informe de diferencias antes de restaurar la versión original.
