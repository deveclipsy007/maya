import requests

url = "http://localhost:8080/message/sendPoll/agente_bot"

payload = {
    "number": "5562998550007",
    "options": {
        "delay": 123,
        "presence": "composing"
    },
    "pollMessage": {
        "name": "Enquete",
        "selectableCount": 2,
        "values": ["Opção 1", "Opção 2"]
    }
}
headers = {
    "apikey": "1234",
    "Content-Type": "application/json"
}

response = requests.request("POST", url, json=payload, headers=headers)

print(response.text)