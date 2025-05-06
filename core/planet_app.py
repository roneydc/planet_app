"""
Classe principal da aplicação Planet App.
"""

import os
import json
import datetime
from planet_app.core.file_manager import FileManager
from planet_app.core.api_handler import PlanetAPIHandler
from planet_app.utils.logging_config import get_logger

logger = get_logger("PlanetApp")

class PlanetApp:
    """Classe principal que gerencia o fluxo da aplicação"""
    
    def __init__(self, api_key=None):
        self.file_manager = FileManager()
        self.api_handler = None
        self.setup_api(api_key) if api_key else None
        logger.info("PlanetApp inicializado")
    
    def setup_api(self, api_key):
        """
        Configura o manipulador da API com a chave fornecida
        
        Args:
            api_key (str): Chave de API da Planet
            
        Returns:
            bool: True se a configuração foi bem-sucedida, False caso contrário
        """
        self.api_handler = PlanetAPIHandler(api_key)
        valid = self.api_handler.validate_api_key()
        if valid:
            self.api_handler.initialize_session()
        return valid
    
    def process_shapefile_to_json(self, shapefile_path=None):
        """
        Processa um shapefile para formato JSON
        
        Args:
            shapefile_path (str, optional): Caminho do arquivo shapefile. 
                                           Se None, abre diálogo para seleção
            
        Returns:
            str: Caminho do arquivo JSON gerado ou None se houve erro
        """
        if not self.api_handler:
            logger.error("API nao inicializada")
            return None
        
        if not shapefile_path:
            shapefile_path = self.file_manager.select_file(("Arquivos Shapefile", "*.shp"))
            if not shapefile_path:
                return None
        
        try:
            # Processar o shapefile
            geojson_data = self.api_handler.process_shapefile(shapefile_path)
            
            # Salvar o resultado
            json_path = self.file_manager.save_json(geojson_data)
            return json_path
        except Exception as e:
            logger.error(f"Erro ao processar shapefile: {e}")
            return None
    
    def search_images(self, json_path, start_date, end_date, cloud_cover):
        """
        Busca imagens com base em um arquivo GeoJSON
        
        Args:
            json_path (str): Caminho do arquivo GeoJSON
            start_date (str): Data de início da busca
            end_date (str): Data de fim da busca
            cloud_cover (float): Cobertura máxima de nuvens (0-1)
            
        Returns:
            tuple: (list de imagens encontradas, str caminho do arquivo de links)
        """
        if not self.api_handler:
            logger.error("API nao inicializada")
            return None, None
        
        try:
            # Carregar o GeoJSON
            with open(json_path, 'r') as f:
                geojson = json.load(f)
            
            # Buscar imagens
            images, download_links = self.api_handler.search_images(
                geojson, start_date, end_date, cloud_cover
            )
            
            # Salvar links para download posterior
            links_file_path = self.file_manager.save_links(download_links)
            
            return images, links_file_path
        except Exception as e:
            logger.error(f"Erro ao buscar imagens: {e}")
            return [], None
    
    def create_order(self, selected_images):
        """
        Cria uma ordem para as imagens selecionadas
        
        Args:
            selected_images (list): Lista de dicionários com informações das imagens
            
        Returns:
            dict: Informações da ordem criada ou None se houve erro
        """
        if not self.api_handler:
            logger.error("API nao inicializada")
            return None
        
        try:
            image_ids = [img["id"] for img in selected_images]
            order = self.api_handler.create_order(image_ids)
            return order
        except Exception as e:
            logger.error(f"Erro ao criar ordem: {e}")
            return None
    
    def download_images(self, links_file=None):
        """
        Baixa imagens a partir de um arquivo de links
        
        Args:
            links_file (str, optional): Caminho do arquivo de links.
                                       Se None, abre diálogo para seleção
            
        Returns:
            list: Lista de caminhos das imagens baixadas ou None se houve erro
        """
        if not self.api_handler:
            logger.error("API nao inicializada")
            return None
        
        if not links_file:
            links_file = self.file_manager.select_file(("Arquivos de texto", "*.txt"))
            if not links_file:
                return None
        
        try:
            # Carregar links
            with open(links_file, 'r') as f:
                links = [line.strip() for line in f.readlines()]
            
            # Baixar cada imagem
            downloaded_files = []
            for i, link in enumerate(links):
                output_path = os.path.join(
                    self.file_manager.images_dir, 
                    f"planet_image_{i}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.tif"
                )
                downloaded_file = self.api_handler.download_image(link, output_path)
                downloaded_files.append(downloaded_file)
            
            return downloaded_files
        except Exception as e:
            logger.error(f"Erro ao baixar imagens: {e}")
            return []