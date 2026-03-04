# ==============================
# IMPORTAÇÕES
# ==============================
from flask import Flask, request, jsonify
import requests, json, os
from flask_cors import CORS

# ==============================
# CONFIGURAÇÕES
# ==============================
TOKEN = os.getenv("TOKEN")          # Coloque seu token do bot aqui
ADMIN_ID = 358280866                 # Seu ID do Telegram
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
CORS(app, resources={r"/dados": {"origins": "*"}})  # Permite acesso do site

# ==============================
# SALVAR DADOS
# ==============================
def salvar_dados(cidade, data):
    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump({"cidade": cidade, "data": data}, f, ensure_ascii=False, indent=4)

# ==============================
# ROTA JSON
# ==============================
@app.route("/dados", methods=["GET"])
def retornar_dados():
    if not os.path.exists("dados.json"):
        return jsonify({"cidade": "", "data": ""})
    with open("dados.json", "r", encoding="utf-8") as f:
        return jsonify(json.load(f))

# ==============================
# WEBHOOK DO TELEGRAM
# ==============================
@app.route("/webhook", methods=["POST"])
def webhook():
    dados = request.get_json()

    # Mensagens normais
    if "message" in dados:
        msg = dados["message"]
        texto = msg.get("text","")
        chat_id = msg["chat"]["id"]
        user_id = msg["from"]["id"]

        if user_id != ADMIN_ID:
            return "Não autorizado", 403

        # /start → mostra menu fixo de botões
        if texto.startswith("/start"):
            teclado = {
                "keyboard": [["📍Update Local"], ["Outra Opção"]],
                "resize_keyboard": True,
                "one_time_keyboard": False
            }
            requests.post(f"{TELEGRAM_URL}/sendMessage",
                json={"chat_id": chat_id,
                      "text":"Escolha uma opção:",
                      "reply_markup": teclado})

        # Botão clicado
        if texto == "📍Update Local":
            requests.post(f"{TELEGRAM_URL}/sendMessage",
                json={"chat_id": chat_id,
                      "text":"📌 Digite: Cidade Data\nEx: Franca-SP 03/04/2026"})

        # Recebe cidade e data digitada e salva
        partes = texto.split()
        if len(partes) == 3 and partes[0] != "/start":
            salvar_dados(partes[0], partes[1])
            requests.post(f"{TELEGRAM_URL}/sendMessage",
                          json={"chat_id": chat_id,
                                "text":"✅ Atualizado com sucesso!"})

    return "OK", 200

# ==============================
# RODAR APLICAÇÃO
# ==============================
if __name__=="__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT",5000)))
