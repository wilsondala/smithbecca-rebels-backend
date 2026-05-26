import os
from typing import Any

from PIL import Image, ImageDraw, ImageFont

BANK_ACCOUNT_NAME = os.getenv("BANK_ACCOUNT_NAME", "WILSON SANTOS KAHANGO DALA")
BANK_NAME = os.getenv("BANK_NAME", "Banco Angolano de Investimentos")
BANK_IBAN = os.getenv("BANK_IBAN", "AO06004000006076803010194")

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
GENERATED_BANK_DIR = os.path.join(STATIC_DIR, "generated", "bank")
TEMPLATE_PATH = os.path.join(STATIC_DIR, "templates", "bank_transfer_template.png")

DEFAULT_WIDTH = 1080
DEFAULT_HEIGHT = 1350

WHITE = (255, 255, 255)
BLACK = (15, 15, 15)


def _safe_text(value: Any, fallback: str = "-") -> str:
    if value is None:
        return fallback
    text = str(value).strip()
    return text if text else fallback


def _ensure_dirs() -> None:
    os.makedirs(GENERATED_BANK_DIR, exist_ok=True)


def _load_font(size: int, bold: bool = False):
    candidates = []

    if bold:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
                "/Library/Fonts/Arial Bold.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ]
        )
    else:
        candidates.extend(
            [
                "/System/Library/Fonts/Supplemental/Arial.ttf",
                "/Library/Fonts/Arial.ttf",
                "C:/Windows/Fonts/arial.ttf",
            ]
        )

    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                pass

    return ImageFont.load_default()


def _clear_value_areas(draw: ImageDraw.ImageDraw) -> None:
    """
    Limpa completamente a área interna do cartão branco
    onde ficam os dados bancários.
    """

    # Área TOTAL do card (onde estão nome, banco e IBAN)
    draw.rectangle((120, 330, 960, 620), fill=(255, 255, 255))


def _draw_bank_info_on_template(image: Image.Image) -> Image.Image:
    draw = ImageDraw.Draw(image)

    # limpa área inteira do card
    _clear_value_areas(draw)

    # fontes
    font_label = _load_font(24, bold=True)
    font_value = _load_font(30, bold=True)

    # 🔹 NOME
    draw.text((180, 360), "NOME", fill=(225, 29, 29), font=font_label)
    draw.text((180, 400), BANK_ACCOUNT_NAME, fill=(15, 15, 15), font=font_value)

    # 🔹 BANCO
    draw.text((180, 470), "BANCO", fill=(225, 29, 29), font=font_label)
    draw.text((180, 510), BANK_NAME, fill=(15, 15, 15), font=font_value)

    # 🔹 IBAN
    # 🔹 IBAN (somente valor, sem repetir label)
    draw.rectangle((300, 540, 960, 600), fill=(255, 255, 255))  # limpa só valor

    draw.text(
        (320, 550),
        BANK_IBAN,
        fill=(15, 15, 15),
        font=_load_font(28, bold=True),
    )

    return image

def _create_fallback_canvas() -> Image.Image:
    """
    Canvas simples caso o template não exista.
    """
    image = Image.new("RGB", (DEFAULT_WIDTH, DEFAULT_HEIGHT), WHITE)
    draw = ImageDraw.Draw(image)

    title_font = _load_font(54, bold=True)
    subtitle_font = _load_font(26, bold=False)
    label_font = _load_font(24, bold=True)
    value_font = _load_font(30, bold=True)

    draw.text((120, 120), "PAGAMENTO POR", fill=BLACK, font=title_font)
    draw.text((120, 200), "TRANSFERÊNCIA BANCÁRIA", fill=(225, 29, 29), font=title_font)
    draw.text(
        (120, 300),
        "Utilize os dados abaixo para concluir o pagamento.",
        fill=BLACK,
        font=subtitle_font,
    )

    draw.text((120, 420), "NOME", fill=(225, 29, 29), font=label_font)
    draw.text((120, 460), _safe_text(BANK_ACCOUNT_NAME), fill=BLACK, font=value_font)

    draw.text((120, 560), "BANCO", fill=(225, 29, 29), font=label_font)
    draw.text((120, 600), _safe_text(BANK_NAME), fill=BLACK, font=value_font)

    draw.text((120, 700), "CONTA / IBAN", fill=(225, 29, 29), font=label_font)
    draw.text((120, 740), _safe_text(BANK_IBAN), fill=BLACK, font=value_font)

    return image


def _render_image() -> Image.Image:
    if os.path.exists(TEMPLATE_PATH):
        try:
            image = Image.open(TEMPLATE_PATH).convert("RGB")
            image = image.resize((DEFAULT_WIDTH, DEFAULT_HEIGHT))
            return _draw_bank_info_on_template(image)
        except Exception:
            pass

    return _create_fallback_canvas()


def generate_bank_image_for_order(order) -> str:
    _ensure_dirs()

    order_id = _safe_text(getattr(order, "id", None), "-")
    filename = f"bank_order_{order_id}.png"
    output_path = os.path.join(GENERATED_BANK_DIR, filename)

    image = _render_image()
    image.save(output_path, format="PNG", optimize=True)

    return filename