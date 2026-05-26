from typing import Any, Dict

from app.services.payment_gateway import get_payment_gateway


def create_express_payment(order_id: int, amount: float) -> Dict[str, Any]:
    """
    Mantido por compatibilidade com a estrutura atual do projeto.

    Internamente, delega para a camada de gateway.
    Assim, o restante do sistema não quebra quando migrarmos do mock
    para a AppyPay real.
    """
    gateway = get_payment_gateway()
    return gateway.create_payment(order_id, amount)