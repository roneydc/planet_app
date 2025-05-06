"""
Módulo para gerenciamento de arquivos e diretórios do Planet App.
"""

import os
import json
import datetime
from tkinter import filedialog
from planet_app.utils.logging_config import get_logger

logger = get_logger("FileManager")

class FileManager:
    """Classe para gerenciar arquivos e diretórios"""
    
    def __init__(self):
        self.output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "output")
        self.json_dir = os.path.join(self.output_dir, "json")
        self.images_dir = os.path.join(self.output_dir, "images")
        self.links_dir = os.path.join(self.output_dir, "links")
        
        # Criar estrutura de diretórios
        for directory in [self.output_dir, self.json_dir, self.images_dir, self.links_dir]:
            if not os.path.exists(directory):
                os.makedirs(directory)
                logger.info(f"Diretorio criado: {directory}")
    
    def select_file(self, file_types, title="Selecionar arquivo"):
        """
        Abre diálogo para seleção de arquivo
        
        Args:
            file_types (tuple): Tupla com descrição e padrão de arquivo (ex: ("Arquivos Shapefile", "*.shp"))
            title (str, optional): Título da janela de diálogo. Default: "Selecionar arquivo"
            
        Returns:
            str: Caminho do arquivo selecionado ou string vazia se cancelado
        """
        return filedialog.askopenfilename(title=title, filetypes=[file_types])
    
    def select_directory(self, title="Selecionar diretório"):
        """
        Abre diálogo para seleção de diretório
        
        Args:
            title (str, optional): Título da janela de diálogo. Default: "Selecionar diretório"
            
        Returns:
            str: Caminho do diretório selecionado ou string vazia se cancelado
        """
        return filedialog.askdirectory(title=title)
    
    def save_json(self, data, filename=None):
        """
        Salva dados em formato JSON
        
        Args:
            data (dict): Dados a serem salvos
            filename (str, optional): Nome do arquivo. Se None, gera um nome com timestamp
            
        Returns:
            str: Caminho completo do arquivo salvo
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"planet_data_{timestamp}.json"
        
        file_path = os.path.join(self.json_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Arquivo JSON salvo: {file_path}")
        return file_path
    
    def save_links(self, links, filename=None):
        """
        Salva links em arquivo de texto
        
        Args:
            links (list): Lista de links a serem salvos
            filename (str, optional): Nome do arquivo. Se None, gera um nome com timestamp
            
        Returns:
            str: Caminho completo do arquivo salvo
        """
        if not filename:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"download_links_{timestamp}.txt"
        
        file_path = os.path.join(self.links_dir, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            for link in links:
                f.write(f"{link}\n")
        
        logger.info(f"Links salvos: {file_path}")
        return file_path
    
    def load_json(self, file_path):
        """
        Carrega dados de um arquivo JSON
        
        Args:
            file_path (str): Caminho do arquivo JSON
            
        Returns:
            dict: Dados carregados do arquivo JSON
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.info(f"Arquivo JSON carregado: {file_path}")
        return data
    
    def load_links(self, file_path):
        """
        Carrega links de um arquivo de texto
        
        Args:
            file_path (str): Caminho do arquivo de texto
            
        Returns:
            list: Lista de links carregados do arquivo
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            links = [line.strip() for line in f.readlines()]
        
        logger.info(f"Links carregados: {file_path}")
        return links