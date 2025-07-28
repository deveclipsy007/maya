"""
🔍 DEBUG WEBHOOK - Captura tudo que chega
"""
from flask import Flask, request, jsonify
import json
from datetime import datetime

app = Flask(__name__)
webhook_count = 0

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "status": "Debug Webhook ativo",
        "webhooks_recebidos": webhook_count,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/webhook", methods=["POST", "GET"])
def webhook():
    global webhook_count
    webhook_count += 1
    
    print(f"\n{'='*60}")
    print(f"🔍 WEBHOOK #{webhook_count} RECEBIDO - {datetime.now()}")
    print(f"{'='*60}")
    
    # Método HTTP
    print(f"📋 Método: {request.method}")
    
    # Headers
    print(f"📋 Headers:")
    for key, value in request.headers:
        print(f"   {key}: {value}")
    
    # Query parameters
    if request.args:
        print(f"📋 Query Params: {dict(request.args)}")
    
    # Body/JSON
    try:
        if request.method == "POST":
            if request.is_json:
                data = request.json
                print(f"📋 JSON Body:")
                print(json.dumps(data, indent=2, ensure_ascii=False))
            else:
                raw_data = request.get_data(as_text=True)
                print(f"📋 Raw Body: {raw_data}")
        else:
            print("📋 GET request - sem body")
    except Exception as e:
        print(f"❌ Erro ao ler body: {e}")
    
    print(f"{'='*60}\n")
    
    return jsonify({
        "status": "received",
        "webhook_number": webhook_count,
        "method": request.method,
        "timestamp": datetime.now().isoformat()
    })

@app.route("/test", methods=["GET"])
def test():
    return jsonify({
        "message": "Debug webhook funcionando!",
        "webhooks_count": webhook_count
    })

if __name__ == "__main__":
    print("🔍 DEBUG WEBHOOK INICIADO")
    print("=" * 40)
    print("📡 Capturando TODOS os webhooks...")
    print("🌐 http://localhost:5000")
    print("=" * 40)
    
    app.run(host="0.0.0.0", port=5000, debug=True)