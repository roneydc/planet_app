"""
Módulo para manipulação da API da Planet.
"""

import datetime
import time
from dateutil import parser
import requests
import os
from planet_app.utils.logging_config import get_logger

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
import json


logger = get_logger("PlanetAPIHandler")

class PlanetAPIHandler:
    """Classe para gerenciar interações com a API da Planet"""
    
    def __init__(self, api_key):
        self.api_key = api_key
        self.session = None
        self.url_base = "https://api.planet.com/data/v1/"
        logger.info("PlanetAPIHandler inicializado")
    
    def initialize_session(self):
        """
        Inicializa a sessão para comunicação com a API e valida a autenticação
        
        Returns:
            bool: True se a sessão foi inicializada com sucesso e a autenticação é válida, False caso contrário
        """
        try:
            # Criar a sessão
            self.session = requests.Session()
            self.session.auth = (self.api_key, '')
            
            # Teste inicial de conexão
            base_response = self.session.get(self.url_base)
            if base_response.status_code != 200:
                logger.error(f"Falha na conexão básica com a API: {base_response.status_code}")
                return False
                
            # Tentar acessar um endpoint protegido que requer autenticação válida
            # Por exemplo, tentar listar os recursos disponíveis ou obter informações do usuário
            auth_test_endpoint = f"{self.url_base}asset-types"  # Endpoint que requer autenticação
            auth_response = self.session.get(auth_test_endpoint)
            
            # Verificar se a resposta indica autenticação bem-sucedida
            if auth_response.status_code == 200:
                logger.info("Sessão API inicializada e autenticação válida")
                return True
            elif auth_response.status_code == 401 or auth_response.status_code == 403:
                logger.error(f"Falha na autenticação com a API: {auth_response.status_code}")
                return False
            else:
                logger.warning(f"Resposta inesperada ao testar autenticação: {auth_response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao inicializar sessão: {e}")
            return False
    
    def validate_api_key(self):
        """
        Valida a chave de API fornecida
        
        Returns:
            bool: True se a chave é válida, False caso contrário
        """
        # Implementação simplificada - aqui você adicionaria a lógica real
        # para validar a chave com a API da Planet
        try:
            if self.api_key and len(self.api_key) > 20:
                # Create session
                if self.initialize_session():
                    logger.info("Chave API validada com sucesso")
                    return True
                else:
                    logger.warning("Falha na conexão com a API")
                    return False
            else:
                logger.warning("Chave API invalida - muito curta")
                return False
        except Exception as e:
            logger.error(f"Erro ao validar chave API: {e}")
            return False
    
    def process_shapefile(self, shapefile_path):
        """
        Processa um arquivo shapefile e converte para GeoJSON com manipulações específicas
        
        Args:
            shapefile_path (str): Caminho do arquivo shapefile
                
        Returns:
            dict: GeoJSON resultante do processamento
        """
        logger.info(f"Processando shapefile: {shapefile_path}")
        
        try:
            # Carregar o shapefile usando geopandas
            gdf_limites = gpd.read_file(shapefile_path)
            
            # Função para simplificar geometria
            def simplificar_geometria(geom):
                # Simplifica a geometria mantendo a topologia, com tolerância de 0.001
                # Ajuste a tolerância conforme necessário
                return geom.simplify(tolerance=0.001, preserve_topology=True)
            
            # Função para remover coordenadas Z
            def remove_z_coordinates(geom):
                if isinstance(geom, Polygon):
                    # Remove coordenadas Z do Polygon, incluindo buracos
                    exterior = [(x, y) for x, y, *_ in geom.exterior.coords]
                    interiors = [[(x, y) for x, y, *_ in interior.coords] for interior in geom.interiors]
                    return Polygon(exterior, interiors)
                elif isinstance(geom, MultiPolygon):
                    # Remove coordenadas Z de cada Polygon no MultiPolygon
                    return MultiPolygon([remove_z_coordinates(p) for p in geom.geoms])
                else:
                    return geom  # Retorna a geometria original caso não seja Polygon ou MultiPolygon
            
            # Aplicar simplificação nas geometrias
            geometrias_simplificadas = [simplificar_geometria(geom) for geom in gdf_limites['geometry']]
            
            # Criar novo GeoDataFrame com geometrias simplificadas
            gdf_simplificado = gpd.GeoDataFrame(geometry=geometrias_simplificadas)
            gdf_simplificado = pd.concat([gdf_limites.drop(columns='geometry'), gdf_simplificado], axis=1)
            gdf_simplificado = gdf_simplificado.set_geometry('geometry')
            
            # Remover coordenadas Z
            gdf_simplificado['geometry'] = gdf_simplificado['geometry'].apply(remove_z_coordinates)
            
            # Converter para GeoJSON
            data = json.loads(gdf_simplificado.to_json())
            
            # Verificar se existem as propriedades necessárias
            features = data.get("features", [])
            
            # Criar um dicionário com "Talhao" como chave
            new_dict = {}
            
            for feature in features:
                properties = feature.get("properties", {})
                
                # Verificar se as propriedades necessárias existem
                if "layer" in properties and "Talhao" in properties:
                    talhao = f'{properties["layer"]}_{properties["Talhao"]}'
                    geometry = feature["geometry"]
                    new_dict[talhao] = geometry
                else:
                    # Usar um identificador genérico se as propriedades não existirem
                    talhao_id = f"talhao_{len(new_dict) + 1}"
                    new_dict[talhao_id] = feature["geometry"]
            logger.info(f"JSON processado com sucesso {len(new_dict)} talhoes encontrados")
            
            # Retornar o resultado como um dicionário
            return new_dict
            
        except Exception as e:
            logger.error(f"Erro ao processar shapefile: {e}")
            # Retornar um GeoJSON vazio em caso de erro
            return {
                "type": "FeatureCollection",
                "features": []
            }
        
    
    def search_images(self, geojson, start_date, end_date, cloud_cover=0.25):
        """
        Busca imagens disponíveis com base em uma área de interesse
        
        Args:
            geojson (dict): GeoJSON representando a área de interesse
            start_date (str): Data de início da busca (formato ISO)
            end_date (str): Data de fim da busca (formato ISO)
            cloud_cover (float, optional): Cobertura máxima de nuvens (0-1). Default: 0.25
            
        Returns:
            tuple: (list de imagens encontradas, list de links para download)
        """
        logger.info(f"Buscando imagens de {start_date} ate {end_date} com cobertura de nuvens <= {cloud_cover}")
        #Defini o cabeçalho da requisição
        headers = {"Content-Type": "application/json","Authorization": "api-key {}".format(self.api_key)}
        
        try:
            # Define o cabeçalho para as solicitações HTTP
            headers = {
                "Content-Type": "application/json", "Authorization": f"api-key {self.api_key}"
            }
            
            # Lista para armazenar resultados
            all_results = []
            download_links = []
            
            # Determinar o método de busca com base no formato do geojson
            if "features" in geojson:
                # Formato GeoJSON padrão com array de features
                features = geojson.get("features", [])
                
                logger.info(f"Processando busca para {len(features)} geometrias no GeoJSON")
                
                for idx, feature in enumerate(features):
                    geometry = feature.get("geometry", {})
                    
                    # Buscar imagens para esta geometria
                    feature_images = self._get_image_ids(
                        geometry, start_date, end_date, cloud_cover, headers
                    )
                    
                    if feature_images:
                        # Adicionar identificador da feature para organização
                        feature_name = f"feature_{idx+1}"
                        if "properties" in feature and feature["properties"]:
                            props = feature["properties"]
                            if "layer" in props and "Talhao" in props:
                                feature_name = f"{props['layer']}_{props['Talhao']}"
                            elif "name" in props:
                                feature_name = props["name"]
                        
                        # Processar resultados
                        for img in feature_images:
                            img_id = img.get("id", "")
                            img_data = self._process_image_result(img, feature_name)
                            all_results.append(img_data)
                            
                            # Adicionar link para download
                            if "_links" in img and "assets" in img["_links"]:
                                download_links.append(img["_links"]["assets"])
                    
                    # Evitar rate limiting
                    time.sleep(0.3)
                    
            elif isinstance(geojson, dict) and all(isinstance(key, str) for key in geojson.keys()):
                # Formato alternativo: dicionário com nome -> geometria
                logger.info(f"Processando busca para {len(geojson)} áreas nomeadas")
                
                for name, geometry in geojson.items():
                    # Buscar imagens para esta geometria
                    feature_images = self._get_image_ids(
                        geometry, start_date, end_date, cloud_cover, headers
                    )
                    
                    if feature_images:
                        # Processar resultados
                        for img in feature_images:
                            img_id = img.get("id", "")
                            img_data = self._process_image_result(img, name)
                            all_results.append(img_data)
                            
                            # Adicionar link para download
                            if "_links" in img and "assets" in img["_links"]:
                                download_links.append(img["_links"]["assets"])
                    
                    # Evitar rate limiting
                    time.sleep(0.3)
            else:
                # Formato não reconhecido
                logger.error("Formato de GeoJSON não reconhecido")
                return [], []
            
            logger.info(f"Busca finalizada. Encontradas {len(all_results)} imagens")
            return all_results, download_links
                
        except Exception as e:
            logger.error(f"Erro ao buscar imagens: {e}")
            return [], []
    def _get_image_ids(self, geometry, start_date, end_date, cloud_cover, headers):
        """
        Busca IDs de imagens da API Planet com base nos critérios fornecidos
        
        Args:
            geometry (dict): Geometria no formato GeoJSON
            start_date (str): Data de início
            end_date (str): Data de fim
            cloud_cover (float): Cobertura máxima de nuvens
            headers (dict): Cabeçalhos HTTP para a requisição
            
        Returns:
            list: Lista de resultados da busca
        """
        # Cria um objeto de consulta (query) para a API da Planet
        query = {
            "item_types": ["PSScene"],
            "filter": {            
                "type": "AndFilter",
                "config": [{
                        "type": "GeometryFilter",
                        "field_name": "geometry",
                        "config": geometry},{
                        "type": "DateRangeFilter",
                        "field_name": "acquired",
                        "config": {
                            "gte": start_date,
                            "lte": end_date}},{
                        "type": "RangeFilter",
                        "field_name": "cloud_cover",
                        "config": {
                            "lte": cloud_cover}},{
                        "type":"PermissionFilter",
                        "config":[
                            "assets:download"]
                    }
                ]
            }
        }
        
        # Converte o objeto de consulta para JSON
        query_json = json.dumps(query)
        
        # Define a URL de solicitação
        url = f"{self.url_base}quick-search"
        
        # Envia a solicitação
        response = requests.post(url, data=query_json, headers=headers)
        
        # Verifica se a solicitação foi bem-sucedida
        if response.status_code == 200:
            # Extrai os resultados
            results = response.json().get("features", [])
            if results:
                return results
        else:
            logger.error(f"Erro na busca de imagens: {response.status_code}, {response.text}")
        
        return []

    def _process_image_result(self, image_data, feature_name=""):
        """
        Processa o resultado de uma imagem retornada pela API
        
        Args:
            image_data (dict): Dados da imagem retornada pela API
            feature_name (str): Nome da feature/área associada
            
        Returns:
            dict: Dados processados da imagem
        """
        properties = image_data.get("properties", {})
        
        # Criar objeto com informações relevantes
        processed_data = {
            "id": image_data.get("id", ""),
            "area_name": feature_name,
            "date": properties.get("acquired", ""),
            "cloud_cover": properties.get("cloud_cover", 1.0),
            "instrument": properties.get("instrument", ""),
            "satellite_id": properties.get("satellite_id", ""),
            "sun_azimuth": properties.get("sun_azimuth", 0),
            "sun_elevation": properties.get("sun_elevation", 0),
            "gsd": properties.get("gsd", 0),  # Ground sample distance (resolução)
            "download_link": ""
        }
        
        # Extrair link de download se disponível
        if "_links" in image_data and "assets" in image_data["_links"]:
            processed_data["download_link"] = image_data["_links"]["assets"]
        
        return processed_data
    
    def create_order(self, selected_images):
        """
        Cria uma ordem de download para as imagens selecionadas usando a API Planet
        
        Args:
            selected_images (list): Lista de dicionários com informações das imagens
            
        Returns:
            dict: Informações da ordem criada ou None se houve erro
        """
        logger.info(f"Criando ordem para {len(selected_images)} imagens")
        
        try:
            # Agrupar imagens por área/talhão
            images_by_area = {}
            for img in selected_images:
                area_name = img.get("area_name", "unknown_area")
                if area_name not in images_by_area:
                    images_by_area[area_name] = {
                        "images": [],
                        "geometry": img.get("geometry", {})
                    }
                images_by_area[area_name]["images"].append(img["id"])
            
            # URL para a API de ordens
            orders_url = 'https://api.planet.com/compute/ops/orders/v2'
            
            # Cabeçalhos para a requisição
            headers = {
                "Content-Type": "application/json"
            }
            
            # Autenticação
            auth = requests.auth.HTTPBasicAuth(self.api_key, '')
            
            # Lista para armazenar respostas das ordens
            order_responses = []
            error_list = []
            
            # Criar uma ordem para cada área
            for area_name, area_data in images_by_area.items():
                try:
                    # Parâmetros da ordem
                    order_params = {
                        "name": area_name,
                        "source_type": "scenes",
                        "order_type": "partial",
                        "products": [
                            {
                                "item_ids": area_data["images"],
                                "item_type": "PSScene",
                                "product_bundle": "analytic_8b_sr_udm2"
                            }
                        ],
                        "tools": [
                            {"clip": {"aoi": area_data["geometry"]}},
                            {"harmonize": {"target_sensor": "Sentinel-2"}},
                            {"reproject": {"projection": "WGS84", "kernel": "cubic"}},
                            {"composite": {"group_by": "strip_id"}},
                            {"bandmath": {
                                "b1": "b1",
                                "b2": "b2",
                                "b3": "b3",
                                "b4": "b4",
                                "b5": "b5",
                                "b6": "b6",
                                "b7": "b7",
                                "b8": "b8",
                                "pixel_type": "32R"
                            }}
                        ],
                        "delivery": {
                            "archive_type": "zip",
                            "archive_filename": "{{name}}_{{order_id}}.zip"
                        }
                    }
                    
                    # Enviar requisição para criar a ordem
                    response = requests.post(
                        orders_url, 
                        data=json.dumps(order_params), 
                        auth=auth, 
                        headers=headers
                    )
                    
                    # Verificar resposta
                    response.raise_for_status()
                    
                    # Adicionar resposta à lista
                    order_response = response.json()
                    order_responses.append({
                        "area_name": area_name,
                        "order_id": order_response.get("id", ""),
                        "status": order_response.get("state", ""),
                        "created_at": datetime.datetime.now().isoformat(),
                        "links": order_response.get("_links", {}),
                        "item_count": len(area_data["images"])
                    })
                    
                    # Pequeno delay para evitar rate limiting
                    time.sleep(0.25)
                    
                except Exception as e:
                    logger.error(f"Erro ao criar ordem para área {area_name}: {e}")
                    error_list.append({
                        "area_name": area_name,
                        "error": str(e)
                    })
            
            # Salvar links das ordens em um arquivo
            self._save_order_links(order_responses)
            
            # Retornar resultados
            return {
                "order_id": f"batch_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}",
                "status": "processing",
                "created_at": datetime.datetime.now().isoformat(),
                "orders": order_responses,
                "errors": error_list,
                "items": [img["id"] for img in selected_images]
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar ordens: {e}")
            return None
        
    def _save_order_links(self, order_responses):
        """
        Salva os links das ordens em um arquivo de texto
        
        Args:
            order_responses (list): Lista de respostas das ordens criadas
        """
        try:
            # Criar nome de arquivo com data atual
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"orders_{timestamp}.txt"
            
            # Caminho do arquivo
            file_path = os.path.join(self.links_dir, filename)
            
            # Escrever links no arquivo
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f"# Ordens criadas em {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                for order in order_responses:
                    f.write(f"Área: {order['area_name']}\n")
                    f.write(f"ID da Ordem: {order['order_id']}\n")
                    f.write(f"Status: {order['status']}\n")
                    f.write(f"Link: {order['links'].get('_self', '')}\n")
                    f.write(f"Número de itens: {order['item_count']}\n")
                    f.write("\n---\n\n")
            
            logger.info(f"Links das ordens salvos em: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Erro ao salvar links das ordens: {e}")
            return None
    
    def download_image(self, download_link, output_path):
        """
        Baixa uma imagem a partir do link fornecido
        
        Args:
            download_link (str): Link para download da imagem
            output_path (str): Caminho onde a imagem será salva
            
        Returns:
            str: Caminho da imagem baixada
        """
        logger.info(f"Baixando imagem: {download_link}")
        
        try:
            # Simulação de download
            time.sleep(3)
            
            # Simula a criação de um arquivo
            with open(output_path, 'w') as f:
                f.write("Conteúdo simulado da imagem")
            
            logger.info(f"Imagem salva em: {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Erro ao baixar imagem: {e}")
            return None