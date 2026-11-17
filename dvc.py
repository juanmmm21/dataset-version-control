"""Compatibilidad: el código vive en el paquete `dataset_version_control`. Este módulo se
conserva para quien añade esta carpeta a `sys.path` e importa `dvc`
directamente."""

from dataset_version_control.dvc import *  # noqa: F401,F403
from dataset_version_control.dvc import DatasetVCS, CommitMetadata  # noqa: F401
