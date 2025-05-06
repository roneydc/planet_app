"""
Aba de download de imagens da GUI do Planet App.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import datetime
from planet_app.utils.logging_config import get_logger

logger = get_logger("DownloadTab")

class DownloadTab:
    """Aba de download de imagens da GUI"""
    
    def __init__(self, parent, main_app):
        """
        Inicializa a aba de download de imagens
        
        Args:
            parent: Widget pai (notebook)
            main_app: Instância principal da aplicação GUI
        """
        self.parent = parent
        self.main_app = main_app
        self.frame = ttk.Frame(parent, padding="10")
        
        # Variáveis de controle
        self.links_path_var = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        self.download_status_var = tk.StringVar()
        self.download_status_var.set("Aguardando início do download...")
        
        # Criar componentes da interface
        self._setup_ui()
        
        logger.info("Aba de download de imagens inicializada")
    
    def _setup_ui(self):
        """Configura os elementos da interface da aba"""
        # Frame para seleção de arquivo de links
        links_frame = ttk.Frame(self.frame, padding="10")
        links_frame.pack(fill=tk.X, pady=10)
        
        ttk.Label(links_frame, text="Arquivo de Links:").pack(anchor=tk.W)
        
        path_frame = ttk.Frame(links_frame)
        path_frame.pack(fill=tk.X, pady=5)
        
        ttk.Entry(path_frame, textvariable=self.links_path_var, width=70).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            path_frame, 
            text="Procurar", 
            command=self._select_links_file
        ).pack(side=tk.LEFT, padx=5)
        
        # Botão para iniciar download
        download_button = ttk.Button(
            links_frame, 
            text="Iniciar Download",
            command=self._download_images
        )
        download_button.pack(pady=10)
        
        # Progress frame
        progress_frame = ttk.LabelFrame(self.frame, text="Progresso", padding="10")
        progress_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Barra de progresso
        self.progress_bar = ttk.Progressbar(
            progress_frame, 
            variable=self.progress_var,
            maximum=100,
            length=700
        )
        self.progress_bar.pack(pady=10)
        
        # Status
        ttk.Label(
            progress_frame, 
            textvariable=self.download_status_var,
            wraplength=700
        ).pack(pady=5)
        
        # Lista de arquivos baixados
        ttk.Label(progress_frame, text="Arquivos baixados:").pack(anchor=tk.W, pady=5)
        
        self.download_list = tk.Listbox(progress_frame, width=80, height=10)
        self.download_list.pack(fill=tk.BOTH, expand=True)
    
    def _select_links_file(self):
        """Seleciona um arquivo de links"""
        links_path = self.main_app.file_manager.select_file(
            ("Arquivos de Texto", "*.txt"),
            "Selecionar Arquivo de Links"
        )
        if links_path:
            self.links_path_var.set(links_path)
    
    def _download_images(self):
        """Baixa imagens a partir de um arquivo de links"""
        if not self.main_app.planet_app or not self.main_app.planet_app.api_handler:
            messagebox.showerror("Erro", "Por favor, configure a API primeiro.")
            self.main_app.notebook.select(0)  # Volta para a aba de configuração
            return
        
        links_path = self.links_path_var.get().strip()
        if not links_path:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo de links.")
            return
        
        # Limpar lista anterior
        self.download_list.delete(0, tk.END)
        self.progress_var.set(0)
        self.download_status_var.set("Iniciando download...")
        
        # Iniciar download em uma thread separada
        def download_thread():
            try:
                # Carregar links
                with open(links_path, 'r') as f:
                    links = [line.strip() for line in f.readlines()]
                
                total_links = len(links)
                downloaded_files = []
                
                # Download de cada imagem
                for i, link in enumerate(links):
                    # Atualizar status na thread principal
                    status_msg = f"Baixando imagem {i+1} de {total_links}..."
                    self.frame.after(0, lambda msg=status_msg: self.download_status_var.set(msg))
                    
                    # Calcular progresso
                    progress = (i / total_links) * 100
                    self.frame.after(0, lambda p=progress: self.progress_var.set(p))
                    
                    # Realizar download
                    output_path = os.path.join(
                        self.main_app.file_manager.images_dir, 
                        f"planet_image_{i}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.tif"
                    )
                    downloaded_file = self.main_app.planet_app.api_handler.download_image(link, output_path)
                    downloaded_files.append(downloaded_file)
                    
                    # Adicionar à lista
                    self.frame.after(0, lambda df=downloaded_file: self.download_list.insert(tk.END, df))
                
                # Finalizar
                self.frame.after(0, lambda: self.progress_var.set(100))
                finish_msg = f"Download concluído! {len(downloaded_files)} arquivos baixados."
                self.frame.after(0, lambda msg=finish_msg: self.download_status_var.set(msg))
                self.frame.after(0, lambda msg=finish_msg: messagebox.showinfo("Sucesso", msg))
                self.frame.after(0, lambda: self.main_app.update_status("Download concluído."))
                
            except Exception as e:
                logger.error(f"Erro ao baixar imagens: {e}")
                # Atualizar UI na thread principal
                self.frame.after(0, lambda: messagebox.showerror("Erro", f"Erro ao baixar imagens: {e}"))
                self.frame.after(0, lambda: self.main_app.update_status("Erro ao baixar imagens."))
        
        threading.Thread(target=download_thread).start()