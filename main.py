#!/usr/bin/env python3
"""
Ponto de entrada principal do Planet App.
"""

import os
import tkinter as tk
import sys


sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from gui.app import PlanetAppGUI
from utils.logging_config import setup_logging

# Carregar variáveis de ambiente do arquivo .env, se existir
from dotenv import load_dotenv
load_dotenv()  # Carrega as variáveis do arquivo .env

def main():
    """Função principal para iniciar a aplicação"""
    # Configurar logging
    setup_logging()
    
    # Iniciar a interface gráfica
    root = tk.Tk()
    app = PlanetAppGUI(root)
    
    # Desabilitar abas até a configuração
    for tab_id in range(1, 4):
        app.notebook.tab(tab_id, state="disabled")
    
    # Verificar por chave de API nas variáveis de ambiente
    if os.environ.get("PL_API_KEY", ""):
        api_key = os.environ.get("PL_API_KEY", "")
    else:
        api_key = "sua_chave_de_api_aqui"  # Substitua pela sua chave de API padrão

    if api_key:
        app.config_tab.api_key_var.set(api_key)
        app.validate_api_key(api_key)
    
    root.mainloop()

if __name__ == "__main__":
    main()