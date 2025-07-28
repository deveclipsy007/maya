"""
🎵 MAYA + WHATSAPP - INTEGRAÇÃO PRONTA!
Sua Maya otimizada já integrada com WhatsApp
"""
import sys
import os
from pathlib import Path

# Adicionar caminho do projeto principal
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# Importar e executar Maya + WhatsApp
from maya_whatsapp import *

if __name__ == "__main__":
    print("🎵 INICIANDO MAYA + WHATSAPP")
    print("=" * 50)
    print("🤖 Maya HopeCann: Carregando...")
    
    try:
        # Inicializar Maya
        maya = get_maya()
        print("✅ Maya carregada com sucesso!")
        
        print("📱 WhatsApp: Configurando...")
        setup_webhook()
        
        print("🌐 API: http://localhost:5000")
        print("=" * 50)
        print("✅ MAYA + WHATSAPP PRONTA!")
        print("🎵 Funcionalidades:")
        print("   • Agendamento de consultas")
        print("   • Respostas com áudio inteligente")
        print("   • Contexto de conversa")
        print("   • Integração WhatsApp completa")
        print("=" * 50)
        print("📋 Para testar:")
        print("   1. python test_maya.py")
        print("   2. Envie mensagem no WhatsApp")
        print("   3. Acesse http://localhost:5000")
        print("=" * 50)
        
        # Inicia servidor
        app.run(host="0.0.0.0", port=5000, debug=False)
        
    except Exception as e:
        print(f"❌ Erro ao inicializar: {e}")
        print("💡 Verifique se o arquivo maya_optimized.py está no diretório pai")
        sys.exit(1)