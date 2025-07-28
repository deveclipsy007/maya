#!/usr/bin/env python3
"""
Maya - Atendente Virtual HopeCann
Ponto de entrada para deploy web (Render, Heroku, etc.)
"""

import os
import sys
from maya_hopecann import app

if __name__ == '__main__':
    # Configuração para deploy web
    port = int(os.environ.get('PORT', 5000))
    host = os.environ.get('HOST', '0.0.0.0')
    
    print("🌿 Maya HopeCann - Deploy Web")
    print(f"🌐 Host: {host}")
    print(f"🔌 Port: {port}")
    print("=" * 50)
    
    app.run(
        host=host,
        port=port,
        debug=False,  # Desabilitado para produção
        threaded=True
    )
