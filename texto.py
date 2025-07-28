import requests

url = "http://localhost:8080/message/sendText/agente_bot"

payload = {
    "number": "5562998550007",
    "textMessage": {"text": "ooi, testando!"}
}
headers = {
    "apikey": "1234",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)