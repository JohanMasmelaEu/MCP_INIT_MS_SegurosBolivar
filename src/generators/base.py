"""Clase base para generadores de proyectos.

Cada stack tecnologico implementa un generador concreto que extiende esta base.
"""

from abc import ABC, abstractmethod
from pathlib import Path

from src.models.project_config import DomainModule, ProjectConfig
from src.utils.file_writer import FileWriter
from src.utils.template_renderer import TemplateRenderer


class BaseGenerator(ABC):
    """Clase base abstracta para generadores de proyectos.

    Define el contrato que cada generador de stack debe implementar.
    """

    def __init__(self, config: ProjectConfig, project_root: Path) -> None:
        """Inicializa el generador.

        Args:
            config: Configuracion completa del proyecto.
            project_root: Ruta donde se genera el proyecto.
        """
        self.config = config
        self.project_root = project_root
        self.writer = FileWriter(project_root)

    @abstractmethod
    def generate(self) -> list[Path]:
        """Genera el proyecto completo.

        Returns:
            Lista de archivos creados.
        """

    @abstractmethod
    def generate_domain_module(self, module: DomainModule) -> list[Path]:
        """Genera un modulo de dominio individual.

        Args:
            module: Configuracion del modulo a generar.

        Returns:
            Lista de archivos creados.
        """

    @abstractmethod
    def regenerate_infrastructure(self) -> list[Path]:
        """Regenera los archivos de infraestructura local.

        Returns:
            Lista de archivos modificados/creados.
        """
