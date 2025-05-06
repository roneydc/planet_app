"""
Configuração de logging para o Planet App.
"""

import logging
import os
from pathlib import Path

def setup_logging():
    """
    Configura o sistema de logging para a aplicação.
    
    Returns:
        logging.Logger: Logger principal configurado
    """
    # Criar diretório para logs se não existir
    log_dir = Path.home() / "planet_app_logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / "planet_app.log"
    
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("PlanetApp")
    logger.info("Logging inicializado")
    
    return logger

def get_logger(name=None):
    """
    Obtém um logger configurado.
    
    Args:
        name (str, optional): Nome do logger. Se None, usa o logger principal.
    
    Returns:
        logging.Logger: Logger configurado
    """
    if name:
        return logging.getLogger(f"PlanetApp.{name}")
    return logging.getLogger("PlanetApp")