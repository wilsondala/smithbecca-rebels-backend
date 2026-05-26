import requests
from fastapi import APIRouter, HTTPException

router = APIRouter(
    prefix="/whatsapp",
    tags=["WhatsApp"]
)

WHATSAPP_TOKEN = "SEU_TOKEN_AQUI"
PHONE_NUMBER_ID = "SEU_PHONE_NUMBER_ID"


@router.post("/send-whatsapp")
def send_whatsapp_message(data: dict):

    # =========================
    # 1️⃣ Validação manual
    # =========================
    phone = data.get("phone")
    message = data.get("message")

    if not phone or not message:
        raise HTTPException(
            status_code=400,
            detail="Campos 'phone' e 'message' são obrigatórios"
        )

    # =========================
    # 2️⃣ Monta URL
    # =========================
    url = f"https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {
            "body": message
        },
    }

    # =========================
    # 3️⃣ Envia requisição
    # =========================
    try:
        response = requests.post(url, headers=headers, json=payload)
        response_data = response.json()

        if response.status_code != 200:
            raise HTTPException(
                status_code=response.status_code,
                detail=response_data
            )

        return {
            "success": True,
            "whatsapp_response": response_data
        }

    except requests.exceptions.RequestException as e:
        raise HTTPException(
            status_code=500,
            detail=f"Erro ao conectar com WhatsApp API: {str(e)}"
        )
