"""
🗄️ Storage Provider - Abstracción para almacenamiento de archivos
Permite cambiar entre local/cloud sin modificar herramientas (SOLID: DIP, OCP)
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
import time
import logging

logger = logging.getLogger("StorageProvider")


class StorageProvider(ABC):
    """Interface para providers de almacenamiento (SOLID: Interface Segregation)"""
    
    @abstractmethod
    def save(self, data: bytes, filename: str) -> str:
        """Guarda datos y retorna path/URL"""
        pass
    
    @abstractmethod
    def get_path(self, filename: str) -> str:
        """Retorna path local o URL del archivo"""
        pass
    
    @abstractmethod
    def delete(self, filename: str) -> bool:
        """Elimina un archivo"""
        pass
    
    @abstractmethod
    def cleanup_old_files(self, days: int) -> int:
        """Elimina archivos más antiguos que X días. Retorna cantidad eliminada."""
        pass


class LocalStorageProvider(StorageProvider):
    """Provider para almacenamiento local en filesystem"""
    
    def __init__(self, base_dir: str, save_files: bool = True):
        """
        Args:
            base_dir: Directorio base para almacenar archivos
            save_files: Si False, los archivos se pueden borrar después de enviar
        """
        self.base_dir = Path(base_dir)
        self.save_files = save_files
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 LocalStorageProvider inicializado: {self.base_dir} (save_files={save_files})")
    
    def save(self, data: bytes, filename: str) -> str:
        """
        Guarda archivo localmente.
        
        Args:
            data: Contenido del archivo en bytes
            filename: Nombre del archivo (sin path)
        
        Returns:
            Path absoluto del archivo guardado
        """
        path = self.base_dir / filename
        
        # Evitar sobrescribir archivos existentes
        if path.exists():
            stem = path.stem
            suffix = path.suffix
            counter = 1
            while path.exists():
                path = self.base_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        
        with open(path, 'wb') as f:
            f.write(data)
        
        logger.info(f"📁 Archivo guardado: {path} ({len(data)} bytes)")
        return str(path)
    
    def get_path(self, filename: str) -> str:
        """Retorna path absoluto del archivo"""
        return str(self.base_dir / filename)
    
    def delete(self, filename: str) -> bool:
        """
        Elimina archivo si existe.
        
        Args:
            filename: Nombre del archivo o path completo
        
        Returns:
            True si se eliminó, False si no existía
        """
        # Soportar tanto filename como path completo
        if '/' in filename or '\\' in filename:
            path = Path(filename)
        else:
            path = self.base_dir / filename
        
        if path.exists():
            path.unlink()
            logger.info(f"🗑️ Archivo eliminado: {path}")
            return True
        else:
            logger.debug(f"⚠️ Archivo no existe para eliminar: {path}")
            return False
    
    def cleanup_old_files(self, days: int) -> int:
        """
        Elimina archivos más antiguos que X días.
        
        Args:
            days: Número de días de antigüedad
        
        Returns:
            Cantidad de archivos eliminados
        """
        cutoff = time.time() - (days * 86400)
        count = 0
        
        for file_path in self.base_dir.glob("*"):
            if file_path.is_file():
                try:
                    # Verificar tiempo de modificación
                    if file_path.stat().st_mtime < cutoff:
                        file_path.unlink()
                        count += 1
                except Exception as e:
                    logger.warning(f"No se pudo eliminar {file_path}: {e}")
        
        if count > 0:
            logger.info(f"🗑️ Limpieza automática: {count} archivo(s) eliminado(s) (>{days} días)")
        
        return count


def get_storage_provider() -> StorageProvider:
    """
    Factory para obtener el storage provider configurado.
    
    Pattern: Factory + Strategy
    
    Returns:
        Instancia del storage provider según configuración
    """
    import config
    
    backend = getattr(config, 'STORAGE_BACKEND', 'local')
    save_files = getattr(config, 'STORAGE_SAVE_FILES', True)
    
    if backend == "local":
        return LocalStorageProvider(
            base_dir=config.EXPORTS_DIR,
            save_files=save_files
        )
    # Futuro: Agregar S3Provider, AzureProvider
    # elif backend == "s3":
    #     return S3StorageProvider(...)
    else:
        raise ValueError(f"Storage backend no soportado: {backend}")
