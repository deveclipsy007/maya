import requests
import base64

with open("imagem.png", "rb") as f:
    arq_binary = f.read()
    arq_base64 = base64.b64encode(arq_binary).decode("utf-8")
    print(arq_base64)

payload = {
    "number": "5562998550007",
    "options": {
        "delay": 123,
        "presence": "composing"
    },
    "mediaMessage": {
        "mediatype": "image",
        "fileName": "imagem.png",
        "caption": "teste",
        "media": arq_base64
    }
}
headers = {
    "apikey": "1234",
    "Content-Type": "application/json"
}

url = "http://localhost:8080/message/sendMedia/agente_bot"

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)