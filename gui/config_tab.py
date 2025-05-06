"""
Aba de configuração da GUI do Planet App.
"""

import tkinter as tk
from tkinter import ttk
from planet_app.utils.logging_config import get_logger

logger = get_logger("ConfigTab")

class ConfigTab:
    """Aba de configuração da GUI"""
    
    def __init__(self, parent, main_app):
        """
        Inicializa a aba de configuração
        
        Args:
            parent: Widget pai (notebook)
            main_app: Instância principal da aplicação GUI
        """
        self.parent = parent
        self.main_app = main_app
        self.frame = ttk.Frame(parent, padding="10")
        
        # Variáveis de controle
        self.api_key_var = tk.StringVar()
        self.show_password_var = tk.BooleanVar()
        self.show_password_var.set(False)
        
        # Criar componentes da interface
        self._setup_ui()
        
        logger.info("Aba de configuração inicializada")
    
    def _setup_ui(self):
        """Configura os elementos da interface da aba"""
        # Frame para entrada da chave API
        api_frame = ttk.Frame(self.frame, padding="10")
        api_frame.pack(fill=tk.X, pady=20)
        
        # Label e entrada para chave API
        ttk.Label(api_frame, text="Chave API Planet:").pack(side=tk.LEFT, padx=5)
        self.api_key_entry = ttk.Entry(api_frame, textvariable=self.api_key_var, width=50, show="*")
        self.api_key_entry.pack(side=tk.LEFT, padx=5)
        
        # Checkbox para mostrar/esconder senha
        ttk.Checkbutton(
            api_frame, 
            text="Mostrar", 
            variable=self.show_password_var,
            command=self._toggle_password_visibility
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão de validação
        ttk.Button(
            api_frame, 
            text="Validar Chave", 
            command=self._validate_api_key
        ).pack(side=tk.LEFT, padx=20)
        
        # Frame para diretórios de saída
        dir_frame = ttk.LabelFrame(self.frame, text="Diretórios de Saída", padding="10")
        dir_frame.pack(fill=tk.X, pady=20, padx=10)
        
        # Informações sobre diretórios
        file_manager = self.main_app.file_manager
        ttk.Label(dir_frame, text=f"Diretório de saída: {file_manager.output_dir}").pack(anchor=tk.W)
        ttk.Label(dir_frame, text=f"Arquivos JSON: {file_manager.json_dir}").pack(anchor=tk.W)
        ttk.Label(dir_frame, text=f"Imagens: {file_manager.images_dir}").pack(anchor=tk.W)
        ttk.Label(dir_frame, text=f"Links: {file_manager.links_dir}").pack(anchor=tk.W)
    
    def _toggle_password_visibility(self):
        """Alterna a visibilidade da senha/chave API"""
        if self.show_password_var.get():
            self.api_key_entry.config(show="")
        else:
            self.api_key_entry.config(show="*")
    
    def _validate_api_key(self):
        """Valida a chave API fornecida"""
        api_key = self.api_key_var.get().strip()
        self.main_app.validate_api_key(api_key)