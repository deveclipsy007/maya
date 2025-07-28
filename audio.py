import requests
import base64

with open("audio.mp3", "rb") as f:
    arq_binary = f.read()
    arq_base64 = base64.b64encode(arq_binary).decode("utf-8")
    print(arq_base64)

url = "http://localhost:8080/message/sendWhatsAppAudio/agente_bot"

payload = {
    "number": "5562998550007",
    "options": {
        "delay": 123,
        "presence": "recording",
        "encoding": True
    },
    "audioMessage": {"audio": arq_base64}
}
headers = {
    "apikey": "1234",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)