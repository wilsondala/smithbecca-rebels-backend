import os
from typing import Optional

import requests

from app.services.bank_image_generator import generate_bank_image_for_order
from app.services.order_message import (
    build_customer_confirmation_message,
    build_order_message,
)

WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_API_VERSION = os.getenv("WHATSAPP_API_VERSION", "v25.0")
ADMIN_PHONE = os.getenv("ADMIN_PHONE")

SEND_CUSTOMER_WHATSAPP = os.getenv("SEND_CUSTOMER_WHATSAPP", "true").lower() == "true"

WHATSAPP_ORDER_TEMPLATE_NAME = os.getenv("WHATSAPP_ORDER_TEMPLATE_NAME", "order_confirmation")
WHATSAPP_ORDER_TEMPLATE_LANG = os.getenv("WHATSAPP_ORDER_TEMPLATE_LANG", "pt_BR")

BANK_ACCOUNT_NAME = os.getenv("BANK_ACCOUNT_NAME", "WILSON SANTOS KAHANGO DALA")
BANK_NAME = os.getenv("BANK_NAME", "Banco Angolano de Investimentos")
BANK_IBAN = os.getenv("BANK_IBAN", "AO06004000006076803010194")

API_PUBLIC_BASE_URL = os.getenv("API_PUBLIC_BASE_URL", "").rstrip("/")

WHATSAPP_RECEIPT_URL = os.getenv(
    "WHATSAPP_RECEIPT_URL",
    "https://wa.me/244954485547?text=Ol%C3%A1%2C%20segue%20o%20meu%20comprovativo%20de%20pagamento."
)


def _normalize_phone(phone: Optional[str]) -> Optional[str]:
    if not phone:
        return None

    cleaned = "".join(ch for ch in str(phone) if ch.isdigit())

    if not cleaned:
        return None

    if cleaned.startswith("244"):
        return cleaned

    if len(cleaned) == 9:
        return f"244{cleaned}"

    return cleaned


def _request_whatsapp(payload: dict) -> dict:
    if not WHATSAPP_TOKEN:
        raise RuntimeError("WHATSAPP_TOKEN não configurado.")

    if not WHATSAPP_PHONE_NUMBER_ID:
        raise RuntimeError("WHATSAPP_PHONE_NUMBER_ID não configurado.")

    url = (
        f"https://graph.facebook.com/"
        f"{WHATSAPP_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    )

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(
        url,
        json=payload,
        headers=headers,
        timeout=30,
    )

    print("WhatsApp status:", response.status_code)
    print("WhatsApp response:", response.text)

    if not response.ok:
        raise RuntimeError(
            f"Erro WhatsApp Cloud API | status={response.status_code} | body={response.text}"
        )

    try:
        return response.json()
    except Exception:
        return {"raw_response": response.text}


def _send_whatsapp_text(to_phone: str, message: str) -> dict:
    normalized_phone = _normalize_phone(to_phone)
    if not normalized_phone:
        raise RuntimeError("Telefone inválido para envio no WhatsApp.")

    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_phone,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message,
        },
    }

    return _request_whatsapp(payload)


def _send_whatsapp_image(to_phone: str, image_url: str, caption: Optional[str] = None) -> dict:
    normalized_phone = _normalize_phone(to_phone)
    if not normalized_phone:
        raise RuntimeError("Telefone inválido para envio de imagem no WhatsApp.")

    if not image_url:
        raise RuntimeError("image_url não configurada para envio de imagem no WhatsApp.")

    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_phone,
        "type": "image",
        "image": {
            "link": image_url,
        },
    }

    if caption:
        payload["image"]["caption"] = caption

    print("[WhatsApp IMG URL]:", image_url)
    print("[WhatsApp IMG PAYLOAD]:", payload)

    return _request_whatsapp(payload)


def _send_whatsapp_cta_url_button(
    to_phone: str,
    button_text: str,
    url: str,
    body_text: str,
    footer_text: Optional[str] = None,
) -> dict:
    normalized_phone = _normalize_phone(to_phone)
    if not normalized_phone:
        raise RuntimeError("Telefone inválido para envio no WhatsApp.")

    if not url:
        raise RuntimeError("WHATSAPP_RECEIPT_URL não configurada.")

    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_phone,
        "type": "interactive",
        "interactive": {
            "type": "cta_url",
            "body": {
                "text": body_text,
            },
            "action": {
                "name": "cta_url",
                "parameters": {
                    "display_text": button_text,
                    "url": url,
                },
            },
        },
    }

    if footer_text:
        payload["interactive"]["footer"] = {"text": footer_text}

    return _request_whatsapp(payload)


def _send_whatsapp_template(
    to_phone: str,
    template_name: str,
    language_code: str,
    body_parameters: list[dict] | None = None,
) -> dict:
    normalized_phone = _normalize_phone(to_phone)
    if not normalized_phone:
        raise RuntimeError("Telefone inválido para envio no WhatsApp.")

    template_payload = {
        "name": template_name,
        "language": {
            "code": language_code,
        },
    }

    if body_parameters:
        template_payload["components"] = [
            {
                "type": "body",
                "parameters": body_parameters,
            }
        ]

    payload = {
        "messaging_product": "whatsapp",
        "to": normalized_phone,
        "type": "template",
        "template": template_payload,
    }

    return _request_whatsapp(payload)


def _get_customer_phone(order) -> Optional[str]:
    if getattr(order, "user", None) and getattr(order.user, "phone", None):
        return order.user.phone

    if getattr(order, "phone", None):
        return order.phone

    if getattr(order, "customer_phone", None):
        return order.customer_phone

    return None


def _get_order_total(order) -> str:
    total = getattr(order, "total", None)
    if total is None:
        total = getattr(order, "total_amount", None)
    return str(total or 0)


def _get_customer_name(order) -> str:
    customer_name = getattr(order, "customer_name", None)
    if not customer_name and getattr(order, "user", None):
        customer_name = getattr(order.user, "name", None)
    return customer_name or "Cliente"


def _get_payment_method_label(order) -> str:
    payment_method = str(getattr(order, "payment_method", "") or "").strip().lower()

    mapping = {
        "transferencia": "Transferência bancária",
        "transferência": "Transferência bancária",
        "bank_transfer": "Transferência bancária",
        "transfer": "Transferência bancária",
        "bank": "Transferência bancária",
        "transferencia bancaria": "Transferência bancária",
        "transferência bancária": "Transferência bancária",
        "transferencia_bancaria": "Transferência bancária",
        "cash_on_delivery": "Pagamento na entrega",
        "entrega": "Pagamento na entrega",
        "card": "Cartão",
        "cartao": "Cartão",
        "cartão": "Cartão",
        "express": "Express",
        "appy_pay": "Appy Pay",
        "appypay": "Appy Pay",
    }

    return mapping.get(
        payment_method,
        str(getattr(order, "payment_method", "") or "Pagamento")
    )


def _is_transfer_payment(order) -> bool:
    payment_method = str(getattr(order, "payment_method", "") or "").strip().lower()

    return payment_method in {
        "transferencia",
        "transferência",
        "bank_transfer",
        "transfer",
        "bank",
        "transferencia bancaria",
        "transferência bancária",
        "transferencia_bancaria",
        "transferência_bancaria",
        "pagamento por transferencia",
        "pagamento por transferência",
        "pagamento_transferencia",
        "pagamento_transferência",
    }


def _build_customer_template_params(order) -> list[dict]:
    customer_name = _get_customer_name(order)
    order_id = str(getattr(order, "id", "") or "")
    total = _get_order_total(order)
    payment_method = _get_payment_method_label(order)

    return [
        {"type": "text", "text": customer_name},
        {"type": "text", "text": order_id},
        {"type": "text", "text": total},
        {"type": "text", "text": payment_method},
    ]


def _build_transfer_payment_text(order) -> str:
    customer_name = _get_customer_name(order)
    total = _get_order_total(order)
    order_id = str(getattr(order, "id", "") or "-")

    return (
        f"💳 *Pagamento via Transferência Bancária*\n\n"
        f"Olá, {customer_name} 👋🏽\n\n"
        f"Para concluir o seu pedido *#{order_id}*, utilize os dados abaixo:\n\n"
        f"🏦 *Dados para pagamento:*\n"
        f"• Nome: *{BANK_ACCOUNT_NAME}*\n"
        f"• Banco: *{BANK_NAME}*\n"
        f"• IBAN: *{BANK_IBAN}*\n\n"
        f"💰 *Valor a pagar:* *{total} Kz*\n\n"
        f"Assim que fizer a transferência, envie o comprovativo pelo botão abaixo."
    )


def _build_transfer_image_caption(order) -> str:
    total = _get_order_total(order)
    order_id = str(getattr(order, "id", "") or "-")

    return (
        f"Pedido #{order_id}\n"
        f"Valor: {total} Kz\n"
        f"Nome: {BANK_ACCOUNT_NAME}\n"
        f"Banco: {BANK_NAME}\n"
        f"IBAN: {BANK_IBAN}"
    )


def _build_generated_bank_image_url(order) -> str:
    if not API_PUBLIC_BASE_URL:
        raise RuntimeError(
            "API_PUBLIC_BASE_URL não configurado. "
            "Use domínio público em produção."
        )

    image_filename = generate_bank_image_for_order(order)

    image_url = f"{API_PUBLIC_BASE_URL}/generated/bank/{image_filename}"

    print("[WhatsApp IMG URL GERADA]:", image_url)

    return image_url


def _send_transfer_payment_flow(order, customer_phone: str) -> None:
    try:
        image_url = _build_generated_bank_image_url(order)
        image_caption = _build_transfer_image_caption(order)

        _send_whatsapp_image(
            to_phone=customer_phone,
            image_url=image_url,
            caption=image_caption,
        )

        print(
            f"[WhatsApp] Cliente enviado imagem bancária dinâmica | pedido #{getattr(order, 'id', '-')}"
        )

    except Exception as image_error:
        print("[WhatsApp AVISO imagem transferência]:", str(image_error))

        customer_message = _build_transfer_payment_text(order)

        try:
            _send_whatsapp_text(customer_phone, customer_message)
            print(
                f"[WhatsApp] Cliente enviado texto bancário (fallback) | pedido #{getattr(order, 'id', '-')}"
            )
        except Exception as text_error:
            print("[WhatsApp ERRO texto transferência]:", str(text_error))

    try:
        _send_whatsapp_cta_url_button(
            to_phone=customer_phone,
            button_text="Enviar comprovativo",
            url=WHATSAPP_RECEIPT_URL,
            body_text="Após realizar a transferência, toque no botão abaixo para enviar o comprovativo.",
            footer_text="Paixão Angola",
        )

        print(
            f"[WhatsApp] Cliente enviado botão de comprovativo | pedido #{getattr(order, 'id', '-')}"
        )

    except Exception as button_error:
        print("[WhatsApp ERRO botão comprovativo]:", str(button_error))


def _send_admin_notification(order) -> None:
    admin_phone = _normalize_phone(ADMIN_PHONE)
    if not admin_phone:
        print("ADMIN_PHONE não configurado corretamente.")
        return

    admin_message = build_order_message(order)
    _send_whatsapp_text(admin_phone, admin_message)

    print(f"[WhatsApp] Admin enviado com sucesso | pedido #{getattr(order, 'id', '-')}")


def _send_customer_notification(order) -> None:
    if not SEND_CUSTOMER_WHATSAPP:
        print("SEND_CUSTOMER_WHATSAPP=false, envio ao cliente ignorado.")
        return

    print("==== DEBUG WHATSAPP CLIENTE ====")
    print("order.id:", getattr(order, "id", None))
    print("order.phone:", getattr(order, "phone", None))
    print("order.customer_phone:", getattr(order, "customer_phone", None))
    print("order.user:", getattr(order, "user", None))
    print(
        "order.user.phone:",
        getattr(getattr(order, "user", None), "phone", None),
    )

    customer_phone_raw = _get_customer_phone(order)
    print("customer_phone_raw:", customer_phone_raw)

    customer_phone = _normalize_phone(customer_phone_raw)
    print("customer_phone_normalized:", customer_phone)

    payment_method = getattr(order, "payment_method", None)
    print("payment_method:", payment_method)
    print("==== FIM DEBUG WHATSAPP CLIENTE ====")

    if not customer_phone:
        print("Cliente sem telefone válido para WhatsApp.")
        return

    try:
        if _is_transfer_payment(order):
            print("→ Fluxo: TRANSFERÊNCIA DETECTADO")
            _send_transfer_payment_flow(order, customer_phone)
        else:
            print("→ Fluxo: NORMAL")
            print("→ NÃO É TRANSFERÊNCIA:", payment_method)
            message = build_customer_confirmation_message(order)
            _send_whatsapp_text(customer_phone, message)

    except Exception as e:
        print("[WhatsApp ERRO envio cliente]:", str(e))

        try:
            if _is_transfer_payment(order):
                fallback_message = _build_transfer_payment_text(order)
            else:
                fallback_message = build_customer_confirmation_message(order)

            _send_whatsapp_text(customer_phone, fallback_message)
            print("[WhatsApp] fallback texto enviado")
        except Exception as fallback_error:
            print("[WhatsApp ERRO fallback]:", str(fallback_error))


def send_order_notifications(order) -> None:
    errors = []

    try:
        _send_admin_notification(order)
    except Exception as e:
        errors.append(f"admin: {str(e)}")
        print("[WhatsApp ERRO admin]:", str(e))

    try:
        _send_customer_notification(order)
    except Exception as e:
        errors.append(f"customer: {str(e)}")
        print("[WhatsApp ERRO cliente]:", str(e))

    if errors:
        print("Falha ao enviar notificações WhatsApp:", " | ".join(errors))