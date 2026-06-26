import os
import shutil
import logging
import hashlib
import json
import time
from typing import Dict, List, Any, Tuple, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class CommitMetadata(BaseModel):
    commit_hash: str
    parent_hash: Optional[str] = None
    message: str
    timestamp: float
    filename: str
    file_hash: str


class DatasetVCS:
    """
    Sistema de Control de Versiones Ligero para Datasets (Data VCS).
    
    Permite versionar archivos de datos (JSON/CSV) mediante snapshots
    basados en hashing MD5, gestionar ramas virtuales y calcular diferencias (diffs)
    de registros agregados, eliminados y modificados para trazabilidad en MLOps.
    """

    def __init__(self, store_dir: str = ".dvc_store") -> None:
        self.store_dir = store_dir
        self.objects_dir = os.path.join(store_dir, "objects")
        self.metadata_file = os.path.join(store_dir, "commits.json")
        self.head_file = os.path.join(store_dir, "head.json")

    def init(self) -> None:
        """Inicializa el repositorio de versionado de datos creando directorios ocultos."""
        os.makedirs(self.store_dir, exist_ok=True)
        os.makedirs(self.objects_dir, exist_ok=True)
        
        if not os.path.exists(self.metadata_file):
            with open(self.metadata_file, "w", encoding="utf-8") as f:
                json.dump({}, f)
                
        if not os.path.exists(self.head_file):
            with open(self.head_file, "w", encoding="utf-8") as f:
                json.dump({"active_branch": "main", "commit_hash": None}, f)

    def _get_head_commit(self) -> Optional[str]:
        """Obtiene el hash del commit apuntado actualmente por HEAD."""
        if not os.path.exists(self.head_file):
            return None
        with open(self.head_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data.get("commit_hash")

    def _update_head(self, commit_hash: str) -> None:
        """Actualiza el puntero de HEAD al commit especificado."""
        with open(self.head_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        data["commit_hash"] = commit_hash
        with open(self.head_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def _load_commits(self) -> Dict[str, Any]:
        """Carga el registro historico de todos los commits."""
        if not os.path.exists(self.metadata_file):
            return {}
        with open(self.metadata_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _save_commit(self, commit: CommitMetadata) -> None:
        """Guarda los metadatos de un nuevo commit en el registro global."""
        commits = self._load_commits()
        commits[commit.commit_hash] = commit.model_dump()
        with open(self.metadata_file, "w", encoding="utf-8") as f:
            json.dump(commits, f, indent=2, ensure_ascii=False)
