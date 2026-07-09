"""Utilidad para escritura segura de archivos en el workspace."""

import logging
import shutil
from pathlib import Path

logger = logging.getLogger("mcp_init_ms.utils.file_writer")


class FileWriter:
    """Escribe archivos renderizados en el workspace del usuario.

    Crea directorios intermedios automaticamente y registra
    todos los archivos creados para el reporte final.
    """

    def __init__(self, base_path: Path) -> None:
        """Inicializa el writer con la ruta base del proyecto.

        Args:
            base_path: Directorio raiz donde se escriben los archivos.
        """
        self.base_path = base_path
        self.created_files: list[Path] = []

    def write(self, relative_path: str, content: str) -> Path:
        """Escribe contenido en un archivo relativo a la base.

        Crea directorios intermedios si no existen.

        Args:
            relative_path: Ruta relativa desde base_path.
            content: Contenido a escribir.

        Returns:
            Path absoluto del archivo creado.
        """
        file_path = self.base_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        self.created_files.append(file_path)
        logger.debug("Archivo creado: %s", file_path)
        return file_path

    def write_binary(self, relative_path: str, content: bytes) -> Path:
        """Escribe contenido binario en un archivo.

        Args:
            relative_path: Ruta relativa desde base_path.
            content: Contenido binario a escribir.

        Returns:
            Path absoluto del archivo creado.
        """
        file_path = self.base_path / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_bytes(content)
        self.created_files.append(file_path)
        logger.debug("Archivo binario creado: %s", file_path)
        return file_path

    def copy_file(self, source: Path, relative_dest: str) -> Path:
        """Copia un archivo fuente al destino relativo.

        Args:
            source: Path absoluto del archivo fuente.
            relative_dest: Ruta relativa de destino desde base_path.

        Returns:
            Path absoluto del archivo copiado.
        """
        dest_path = self.base_path / relative_dest
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest_path)
        self.created_files.append(dest_path)
        logger.debug("Archivo copiado: %s -> %s", source, dest_path)
        return dest_path

    def create_directory(self, relative_path: str) -> Path:
        """Crea un directorio (y padres) sin escribir archivo.

        Args:
            relative_path: Ruta relativa del directorio.

        Returns:
            Path absoluto del directorio creado.
        """
        dir_path = self.base_path / relative_path
        dir_path.mkdir(parents=True, exist_ok=True)
        return dir_path

    def get_created_files(self) -> list[Path]:
        """Retorna la lista de todos los archivos creados.

        Returns:
            Lista de paths absolutos.
        """
        return list(self.created_files)

    def get_created_files_relative(self) -> list[str]:
        """Retorna la lista de archivos creados como rutas relativas.

        Returns:
            Lista de strings con rutas relativas a base_path.
        """
        return [str(f.relative_to(self.base_path)) for f in self.created_files]
