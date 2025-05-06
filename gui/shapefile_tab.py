"""
Aba de processamento de shapefile da GUI do Planet App.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
from planet_app.utils.logging_config import get_logger

logger = get_logger("ShapefileTab")

class ShapefileTab:
    """Aba de processamento de shapefile da GUI"""
    
    def __init__(self, parent, main_app):
        """
        Inicializa a aba de processamento de shapefile
        
        Args:
            parent: Widget pai (notebook)
            main_app: Instância principal da aplicação GUI
        """
        self.parent = parent
        self.main_app = main_app
        self.frame = ttk.Frame(parent, padding="10")
        
        # Variáveis de controle
        self.shapefile_path_var = tk.StringVar()
        self.shapefile_result_var = tk.StringVar()
        
        # Criar componentes da interface
        self._setup_ui()
        
        logger.info("Aba de processamento de shapefile inicializada")
    
    def _setup_ui(self):
        """Configura os elementos da interface da aba"""
        # Frame para seleção de shapefile
        shapefile_frame = ttk.Frame(self.frame, padding="10")
        shapefile_frame.pack(fill=tk.X, pady=20)
        
        # Label e campo de entrada para o caminho do shapefile
        ttk.Label(shapefile_frame, text="Shapefile:").pack(anchor=tk.W)
        
        path_frame = ttk.Frame(shapefile_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(path_frame, textvariable=self.shapefile_path_var, width=70).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            path_frame, 
            text="Procurar", 
            command=self._select_shapefile
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão para processar
        process_button = ttk.Button(
            shapefile_frame, 
            text="Processar Shapefile para JSON",
            command=self._process_shapefile
        )
        process_button.pack(pady=20)
        
        # Frame para exibir resultado
        self.shapefile_result_frame = ttk.LabelFrame(self.frame, text="Resultado", padding="10")
        self.shapefile_result_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        ttk.Label(
            self.shapefile_result_frame, 
            textvariable=self.shapefile_result_var,
            wraplength=700
        ).pack(anchor=tk.W)
    
    def _select_shapefile(self):
        """Seleciona um arquivo shapefile"""
        shapefile_path = self.main_app.file_manager.select_file(
            ("Arquivos Shapefile", "*.shp"), 
            "Selecionar Shapefile"
        )
        if shapefile_path:
            self.shapefile_path_var.set(shapefile_path)
    
    def _process_shapefile(self):
        """Processa o shapefile selecionado"""
        if not self.main_app.planet_app or not self.main_app.planet_app.api_handler:
            messagebox.showerror("Erro", "Por favor, configure a API primeiro.")
            self.main_app.notebook.select(0)  # Volta para a aba de configuração
            return
        
        shapefile_path = self.shapefile_path_var.get().strip()
        if not shapefile_path:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo shapefile.")
            return
        
        # Iniciar processamento em uma thread separada
        self.main_app.update_status("Processando shapefile...")
        
        def process_thread():
            try:
                json_path = self.main_app.planet_app.process_shapefile_to_json(shapefile_path)
                
                # Atualizar UI na thread principal
                self.frame.after(0, lambda: self._update_shapefile_result(json_path))
            except Exception as e:
                logger.error(f"Erro ao processar shapefile: {e}")
                # Atualizar UI na thread principal
                self.frame.after(0, lambda: messagebox.showerror("Erro", f"Erro ao processar shapefile: {e}"))
                self.frame.after(0, lambda: self.main_app.update_status("Erro ao processar shapefile."))
        
        threading.Thread(target=process_thread).start()
    
    def _update_shapefile_result(self, json_path):
        """
        Atualiza o resultado do processamento do shapefile
        
        Args:
            json_path (str): Caminho do arquivo JSON gerado
        """
        if json_path:
            self.shapefile_result_var.set(f"Arquivo JSON gerado com sucesso:\n{json_path}")
            self.main_app.update_status("Shapefile processado com sucesso.")
            
            # Preencher automaticamente o campo na aba de busca
            self.main_app.search_tab.json_path_var.set(json_path)
            
            # Perguntar ao usuário se deseja continuar para a próxima etapa
            if messagebox.askyesno("Sucesso", "Deseja continuar para a busca de imagens?"):
                self.main_app.notebook.select(2)  # Vai para a aba de busca
        else:
            self.shapefile_result_var.set("Erro ao processar o shapefile.")
            self.main_app.update_status("Erro ao processar shapefile.")