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

    def commit(self, filepath: str, message: str) -> str:
        """
        Crea una instantanea (snapshot) del archivo de datos y la registra en el historial.
        
        Args:
            filepath: Ruta al archivo de datos a versionar.
            message: Descripcion explicativa de los cambios.
            
        Returns:
            El hash del commit generado.
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"El archivo de datos '{filepath}' no existe.")
            
        # 1. Calcular hash MD5 del contenido del archivo
        hasher = hashlib.md5()
        with open(filepath, "rb") as f:
            buf = f.read()
            hasher.update(buf)
        file_hash = hasher.hexdigest()
        
        parent_hash = self._get_head_commit()
        
        # Evitamos crear commits duplicados identicos si el HEAD ya apunta al mismo contenido
        if parent_hash:
            commits = self._load_commits()
            if commits.get(parent_hash, {}).get("file_hash") == file_hash:
                logger.info("El contenido del dataset no ha cambiado. Commit omitido.")
                return parent_hash
                
        # 2. Copiar snapshot del archivo al almacen de objetos oculto
        snapshot_filename = f"{file_hash}.dat"
        snapshot_path = os.path.join(self.objects_dir, snapshot_filename)
        shutil.copy2(filepath, snapshot_path)
        
        # 3. Crear identificador unico de commit (basado en hash de metadatos)
        timestamp = time.time()
        commit_hasher = hashlib.sha1()
        commit_hasher.update(f"{parent_hash}{file_hash}{message}{timestamp}".encode("utf-8"))
        commit_hash = commit_hasher.hexdigest()
        
        commit_meta = CommitMetadata(
            commit_hash=commit_hash,
            parent_hash=parent_hash,
            message=message,
            timestamp=timestamp,
            filename=os.path.basename(filepath),
            file_hash=file_hash
        )
        
        # 4. Guardar metadatos y actualizar punteros
        self._save_commit(commit_meta)
        self._update_head(commit_hash)
        
        logger.info(f"Dataset versionado. Commit: {commit_hash[:8]} | Hash del archivo: {file_hash[:8]}")
        return commit_hash

    def checkout(self, commit_hash: str, target_filepath: str) -> None:
        """
        Restaura el dataset al estado de un commit especifico del historial.
        """
        commits = self._load_commits()
        if commit_hash not in commits:
            raise KeyError(f"El commit '{commit_hash}' no existe en el historial de datos.")
            
        file_hash = commits[commit_hash]["file_hash"]
        snapshot_filename = f"{file_hash}.dat"
        snapshot_path = os.path.join(self.objects_dir, snapshot_filename)
        
        if not os.path.exists(snapshot_path):
            raise FileNotFoundError(f"Objeto de datos corrupto. No se encontro snapshot: {snapshot_path}")
            
        # Restauramos el archivo a la ruta de trabajo
        shutil.copy2(snapshot_path, target_filepath)
        self._update_head(commit_hash)
        logger.info(f"Dataset restaurado exitosamente al commit: {commit_hash[:8]}")


