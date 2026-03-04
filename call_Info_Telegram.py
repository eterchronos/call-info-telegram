# ==============================
# IMPORTAÇÕES
# ==============================

from flask import Flask, request, jsonify
import requests
import json
import os
from flask_cors import CORS

# ==============================
# CONFIGURAÇÕES
# ==============================

TOKEN = os.getenv("TOKEN")  # seu token do bot
ADMIN_ID = 358280866        # seu ID
TELEGRAM_URL = f"https://api.telegram.org/bot{TOKEN}"

app = Flask(__name__)
CORS(app, resources={r"/dados": {"origins": "*"}})  # permite qualquer site acessar /dados

# ==============================
# SALVAR DADOS
# ==============================

def salvar_dados(cidade, data):
    dados = {"cidade": cidade, "data": data}
    with open("dados.json", "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=4)

# ==============================
# ROTA JSON
# ==============================

@app.route("/dados", methods=["GET"])
def retornar_dados():
    if not os.path.exists("dados.json"):
        return jsonify({"cidade": "", "data": ""})
    with open("dados.json", "r", encoding="utf-8") as f:
        dados = json.load(f)
    return jsonify(dados)

# ==============================
# WEBHOOK TELEGRAM
# ==============================

@app.route("/webhook", methods=["POST"])
def webhook():
    dados_recebidos = request.get_json()

    # --- MENSAGENS ---
    if "message" in dados_recebidos:
        mensagem = dados_recebidos["message"]
        texto = mensagem.get("text", "")
        usuario_id = mensagem["from"]["id"]
        chat_id = mensagem["chat"]["id"]

        if usuario_id != ADMIN_ID:
            return "Não autorizado", 403

        # /start envia botão via JSON
        if texto.startswith("/start"):
            keyboard = {
                "inline_keyboard": [
                    [{"text": "📍Update Local", "callback_data": "update_local"}]
                ]
            }
            requests.post(
                f"{TELEGRAM_URL}/sendMessage",
                json={
                    "chat_id": chat_id,
                    "text": "Clique no botão abaixo para atualizar Cidade e Data:\n\n"
                            "Depois digite no chat: Cidade Data\nEx: Franca-SP 03/04/2026",
                    "reply_markup": keyboard
                }
            )

        # /atualizar manual
        if texto.startswith("/atualizar"):
            partes = texto.split()
            if len(partes) == 3:
                cidade = partes[1]
                data = partes[2]
                salvar_dados(cidade, data)
                requests.post(
                    f"{TELEGRAM_URL}/sendMessage",
                    json={"chat_id": chat_id, "text": "✅ Atualizado com sucesso!"}
                )
            else:
                requests.post(
                    f"{TELEGRAM_URL}/sendMessage",
                    json={"chat_id": chat_id, "text": "⚠️ Use: /atualizar Cidade Data"}
                )

    # --- CLIQUE DO BOTÃO ---
    if "callback_query" in dados_recebidos:
        query = dados_recebidos["callback_query"]
        user_id = query["from"]["id"]
        data_cb = query["data"]
        chat_id_cb = query["message"]["chat"]["id"]

        if user_id != ADMIN_ID:
            return "Não autorizado", 403

        if data_cb == "update_local":
            requests.post(
                f"{TELEGRAM_URL}/sendMessage",
                json={
                    "chat_id": chat_id_cb,
                    "text": "📌 Para atualizar, digite no chat: Cidade Data\nExemplo:\nFranca-SP 03/04/2026"
                }
            )
            requests.post(
                f"{TELEGRAM_URL}/answerCallbackQuery",
                json={"callback_query_id": query["id"], "text": "Pronto! Digite a Cidade e Data 👆"}
            )

    return "OK", 200

# ==============================
# RODAR APLICAÇÃO
# ==============================

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
