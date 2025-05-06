"""
Configuração de logging para o Planet App.
"""

import logging
import os
from pathlib import Path
import sys

def setup_logging():
    """
    Configura o sistema de logging para a aplicação.
    Os logs serão armazenados no mesmo diretório que o arquivo main.py
    
    Returns:
        logging.Logger: Logger principal configurado
    """
    
    # Determinar o diretório base a partir do local do arquivo atual
    # ou do __main__ se estiver executando como um módulo
    if getattr(sys, 'frozen', False):
        # Se estiver rodando como executável empacotado (ex: PyInstaller)
        base_dir = os.path.dirname(sys.executable)
    else:
        # Se estiver rodando como script ou módulo
        if '__main__' in sys.modules:
            main_module = sys.modules['__main__']
            if hasattr(main_module, '__file__'):
                # Obtém o diretório do arquivo main.py
                base_dir = os.path.dirname(os.path.abspath(main_module.__file__))
            else:
                # Fallback para o diretório atual se não puder determinar o arquivo
                base_dir = os.path.abspath(os.getcwd())
        else:
            # Fallback para o diretório atual
            base_dir = os.path.abspath(os.getcwd())
    
    # Criar diretório de logs se não existir
    log_dir = os.path.join(base_dir, "logs")
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    
    log_file = os.path.join(log_dir, "planet_app.log")
    
    # Configuração de logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logger = logging.getLogger("PlanetApp")
    logger.info(f"Logging inicializado. Arquivo de log: {log_file}")
    
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