"""
Classe principal da GUI do Planet App.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from planet_app.core.planet_app import PlanetApp
from planet_app.core.file_manager import FileManager
from planet_app.gui.config_tab import ConfigTab
from planet_app.gui.shapefile_tab import ShapefileTab
from planet_app.gui.search_tab import SearchTab
from planet_app.gui.download_tab import DownloadTab
from planet_app.utils.logging_config import get_logger

logger = get_logger("GUI")

class PlanetAppGUI:
    """Interface gráfica para o PlanetApp"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Planet API Manager")
        self.root.geometry("800x700")
        self.planet_app = None
        self.file_manager = FileManager()
        
        # Configuração de estilo
        self.setup_styles()
        
        # Frame principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Notebook para abas
        self.notebook = ttk.Notebook(self.main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Aguardando configuração...")
        self.status_bar = ttk.Label(self.root, textvariable=self.status_var, relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Inicializar componentes
        self.init_tabs()
        
        logger.info("Interface grafica inicializada")
    
    def setup_styles(self):
        """Configura os estilos da interface"""
        self.style = ttk.Style()
        self.style.configure("TButton", padding=5, relief="flat", background="#007bff")
        self.style.configure("TFrame", background="#f8f9fa")
        self.style.configure("TLabel", background="#f8f9fa")
    
    def init_tabs(self):
        """Inicializa as abas da aplicação"""
        # Criar instância do PlanetApp
        self.planet_app = PlanetApp()
        
        # Abas
        self.config_tab = ConfigTab(self.notebook, self)
        self.shapefile_tab = ShapefileTab(self.notebook, self)
        self.search_tab = SearchTab(self.notebook, self)
        self.download_tab = DownloadTab(self.notebook, self)
        
        # Adicionar abas ao notebook
        self.notebook.add(self.config_tab.frame, text="Configuração")
        self.notebook.add(self.shapefile_tab.frame, text="Shapefile")
        self.notebook.add(self.search_tab.frame, text="Buscar Imagens")
        self.notebook.add(self.download_tab.frame, text="Download")
    
    def validate_api_key(self, api_key):
        """
        Valida a chave API fornecida
        
        Args:
            api_key (str): Chave API a ser validada
            
        Returns:
            bool: True se a chave for válida, False caso contrário
        """
        if not api_key:
            messagebox.showerror("Erro", "Por favor, insira uma chave API.")
            return False
        
        # Configurar API com a chave
        valid = self.planet_app.setup_api(api_key)
        
        if valid:
            messagebox.showinfo("Sucesso", "Chave API validada com sucesso!")
            self.status_var.set("Chave API validada. Pronto para uso.")
            # Habilitar outras abas
            for tab_id in range(1, 4):
                self.notebook.tab(tab_id, state="normal")
            return True
        else:
            messagebox.showerror("Erro", "Chave API inválida ou erro de conexão.")
            self.status_var.set("Erro na validação da chave API.")
            return False
    
    def update_status(self, message):
        """
        Atualiza a mensagem na barra de status
        
        Args:
            message (str): Mensagem a ser exibida
        """
        self.status_var.set(message)