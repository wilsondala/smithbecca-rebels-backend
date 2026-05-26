from urllib.parse import quote_plus

def generate_whatsapp_link(phone: str, message: str) -> str:
    phone = phone.replace("+", "").replace(" ", "")
    encoded_message = quote_plus(message)
    return f"https://wa.me/{phone}?text={encoded_message}"
