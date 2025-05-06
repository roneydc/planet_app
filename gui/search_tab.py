"""
Aba de busca de imagens da GUI do Planet App.
"""

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import datetime
from planet_app.utils.logging_config import get_logger

logger = get_logger("SearchTab")

class SearchTab:
    """Aba de busca de imagens da GUI"""
    
    def __init__(self, parent, main_app):
        """
        Inicializa a aba de busca de imagens
        
        Args:
            parent: Widget pai (notebook)
            main_app: Instância principal da aplicação GUI
        """
        self.parent = parent
        self.main_app = main_app
        self.frame = ttk.Frame(parent, padding="10")
        
        # Variáveis de controle
        self.json_path_var = tk.StringVar()
        self.start_date_var = tk.StringVar()
        self.start_date_var.set(datetime.datetime.now().strftime("%Y-%m-%d"))
        self.end_date_var = tk.StringVar()
        self.end_date_var.set((datetime.datetime.now() + datetime.timedelta(days=7)).strftime("%Y-%m-%d"))
        self.cloud_cover_var = tk.DoubleVar()
        self.cloud_cover_var.set(0.25)
        self.cloud_value_var = tk.StringVar()
        self.cloud_value_var.set("0.25")
        
        # Armazenar imagens encontradas
        self.found_images = []
        
        # Criar componentes da interface
        self._setup_ui()
        
        logger.info("Aba de busca de imagens inicializada")
    
    def _setup_ui(self):
        """Configura os elementos da interface da aba"""
        # Frame para parâmetros de busca
        search_params_frame = ttk.LabelFrame(self.frame, text="Parâmetros de Busca", padding="10")
        search_params_frame.pack(fill=tk.X, pady=10, padx=10)
        
        # Seleção de arquivo JSON
        json_frame = ttk.Frame(search_params_frame)
        json_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(json_frame, text="Arquivo GeoJSON:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(json_frame, textvariable=self.json_path_var, width=50).pack(side=tk.LEFT, padx=5)
        ttk.Button(
            json_frame, 
            text="Procurar", 
            command=self._select_json_file
        ).pack(side=tk.LEFT, padx=5)
        
        # Datas de início e fim
        date_frame = ttk.Frame(search_params_frame)
        date_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(date_frame, text="Data de início:").pack(side=tk.LEFT, padx=5)
        ttk.Entry(date_frame, textvariable=self.start_date_var, width=20).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(date_frame, text="Data de fim:").pack(side=tk.LEFT, padx=15)
        ttk.Entry(date_frame, textvariable=self.end_date_var, width=20).pack(side=tk.LEFT, padx=5)
        
        # Cobertura de nuvens
        cloud_frame = ttk.Frame(search_params_frame)
        cloud_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(cloud_frame, text="Cobertura máxima de nuvens:").pack(side=tk.LEFT, padx=5)
        cloud_scale = ttk.Scale(
            cloud_frame, 
            from_=0.0, 
            to=1.0, 
            variable=self.cloud_cover_var,
            length=300,
            command=lambda x: self.cloud_value_var.set(f"{float(x):.2f}")
        )
        cloud_scale.pack(side=tk.LEFT, padx=5)
        
        ttk.Label(cloud_frame, textvariable=self.cloud_value_var, width=5).pack(side=tk.LEFT, padx=5)
        
        # Botão de busca
        search_button = ttk.Button(
            search_params_frame, 
            text="Buscar Imagens",
            command=self._search_images
        )
        search_button.pack(pady=10)
        
        # Frame para resultados
        self.search_results_frame = ttk.LabelFrame(self.frame, text="Resultados da Busca", padding="10")
        self.search_results_frame.pack(fill=tk.BOTH, expand=True, pady=10, padx=10)
        
        # Lista de imagens encontradas
        self.images_tree = ttk.Treeview(
            self.search_results_frame,
            columns=("ID", "Data", "Cobertura de Nuvens"),
            show="headings"
        )
        self.images_tree.heading("ID", text="ID da Imagem")
        self.images_tree.heading("Data", text="Data")
        self.images_tree.heading("Cobertura de Nuvens", text="Cobertura de Nuvens")
        
        self.images_tree.column("ID", width=250)
        self.images_tree.column("Data", width=180)
        self.images_tree.column("Cobertura de Nuvens", width=150)
        
        self.images_tree.pack(fill=tk.BOTH, expand=True)
        
        # Botão para criar ordem
        order_frame = ttk.Frame(self.frame)
        order_frame.pack(fill=tk.X, pady=10, padx=10)
        
        ttk.Button(
            order_frame, 
            text="Criar Ordem de Download",
            command=self._create_order
        ).pack(side=tk.RIGHT)
    
    def _select_json_file(self):
        """Seleciona um arquivo JSON"""
        json_path = self.main_app.file_manager.select_file(
            ("Arquivos JSON", "*.json"),
            "Selecionar Arquivo GeoJSON"
        )
        if json_path:
            self.json_path_var.set(json_path)
    
    def _search_images(self):
        """Busca imagens com base nos parâmetros fornecidos"""
        if not self.main_app.planet_app or not self.main_app.planet_app.api_handler:
            messagebox.showerror("Erro", "Por favor, configure a API primeiro.")
            self.main_app.notebook.select(0)  # Volta para a aba de configuração
            return
        
        json_path = self.json_path_var.get().strip()
        if not json_path:
            messagebox.showerror("Erro", "Por favor, selecione um arquivo GeoJSON.")
            return
        
        try:
            # Formatar datas
            start_date = f"{self.start_date_var.get()}T00:00:00.00Z"
            end_date = f"{self.end_date_var.get()}T23:59:59.99Z"
            cloud_cover = self.cloud_cover_var.get()
            
            # Limpar tabela anterior
            for item in self.images_tree.get_children():
                self.images_tree.delete(item)
            
            self.main_app.update_status("Buscando imagens...")
            
            # Iniciar busca em uma thread separada
            def search_thread():
                try:
                    images, links_file_path = self.main_app.planet_app.search_images(
                        json_path, start_date, end_date, cloud_cover
                    )
                    
                    # Atualizar UI na thread principal
                    self.frame.after(0, lambda: self._update_search_results(images, links_file_path))
                except Exception as e:
                    logger.error(f"Erro ao buscar imagens: {e}")
                    # Atualizar UI na thread principal
                    self.frame.after(0, lambda: messagebox.showerror("Erro", f"Erro ao buscar imagens: {e}"))
                    self.frame.after(0, lambda: self.main_app.update_status("Erro ao buscar imagens."))
            
            threading.Thread(target=search_thread).start()
        except Exception as e:
            logger.error(f"Erro ao configurar busca: {e}")
            messagebox.showerror("Erro", f"Erro ao configurar busca: {e}")
    
    def _update_search_results(self, images, links_file_path):
        """
        Atualiza os resultados da busca de imagens
        
        Args:
            images (list): Lista de imagens encontradas
            links_file_path (str): Caminho do arquivo de links salvo
        """
        if not images or not links_file_path:
            self.main_app.update_status("Nenhuma imagem encontrada.")
            return
        
        # Armazenar imagens para uso posterior
        self.found_images = images
        
        # Preencher a tabela com as imagens encontradas
        for img in images:
            self.images_tree.insert(
                "", 
                "end", 
                values=(
                    img["id"], 
                    img["date"].strftime("%Y-%m-%d %H:%M:%S"), 
                    f"{img['cloud_cover']:.2f}"
                )
            )
        
        self.main_app.update_status(f"{len(images)} imagens encontradas. Links salvos em: {links_file_path}")
        
        # Preencher automaticamente o campo na aba de download
        self.main_app.download_tab.links_path_var.set(links_file_path)
        
        # Perguntar ao usuário se deseja criar uma ordem
        if messagebox.askyesno("Sucesso", "Deseja criar uma ordem de download para estas imagens?"):
            self._create_order()
    
    def _create_order(self):
        """Cria uma ordem para as imagens selecionadas"""
        if not self.found_images:
            messagebox.showerror("Erro", "Nenhuma imagem encontrada. Por favor, faça uma busca primeiro.")
            return
        
        # Verificar se há itens selecionados na tabela
        selected_items = self.images_tree.selection()
        
        if not selected_items:
            # Se nenhum item estiver selecionado, usar todas as imagens
            selected_images = self.found_images
            message = "Nenhuma imagem específica selecionada. Criando ordem para todas as imagens."
            messagebox.showinfo("Informação", message)
        else:
            # Obter apenas as imagens selecionadas
            selected_indices = [self.images_tree.index(item) for item in selected_items]
            selected_images = [self.found_images[i] for i in selected_indices]
        
        self.main_app.update_status(f"Criando ordem para {len(selected_images)} imagens...")
        
        # Criar ordem em uma thread separada
        def order_thread():
            try:
                order = self.main_app.planet_app.create_order(selected_images)
                
                # Atualizar UI na thread principal
                self.frame.after(0, lambda: self._update_order_result(order))
            except Exception as e:
                logger.error(f"Erro ao criar ordem: {e}")
                # Atualizar UI na thread principal
                self.frame.after(0, lambda: messagebox.showerror("Erro", f"Erro ao criar ordem: {e}"))
                self.frame.after(0, lambda: self.main_app.update_status("Erro ao criar ordem."))
        
        threading.Thread(target=order_thread).start()
    
    def _update_order_result(self, order):
        """
        Atualiza o resultado da criação de ordem
        
        Args:
            order (dict): Informações da ordem criada
        """
        if not order:
            self.main_app.update_status("Erro ao criar ordem.")
            return
        
        message = (
            f"Ordem criada com sucesso!\n\n"
            f"ID da Ordem: {order['order_id']}\n"
            f"Status: {order['status']}\n"
            f"Criada em: {order['created_at']}\n"
            f"Número de itens: {len(order['items'])}\n\n"
            f"Aguarde pelo menos 15 minutos antes de iniciar o download."
        )
        
        messagebox.showinfo("Ordem Criada", message)
        self.main_app.update_status(f"Ordem {order['order_id']} criada com sucesso.")
        
        # Perguntar ao usuário se deseja continuar para a próxima etapa
        if messagebox.askyesno("Sucesso", "Deseja continuar para a etapa de download?"):
            self.main_app.notebook.select(3)  # Vai para a aba de download