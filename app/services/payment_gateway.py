import uuid
from typing import Any, Dict


class PaymentGateway:
    """
    Camada de abstração para gateways de pagamento.
    """

    def create_payment(self, order_id: int, amount: float) -> Dict[str, Any]:
        raise NotImplementedError

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError


class MockGateway(PaymentGateway):
    """
    Gateway local temporário.
    Simula criação de pagamento Express/MCX.
    """

    def create_payment(self, order_id: int, amount: float) -> Dict[str, Any]:
        normalized_amount = round(float(amount or 0), 2)

        if normalized_amount <= 0:
            raise ValueError("Valor do pagamento deve ser maior que zero")

        reference = f"EXP-{uuid.uuid4().hex[:10].upper()}"

        return {
            "provider": "mock",
            "order_id": order_id,
            "reference": reference,
            "amount": normalized_amount,
            "currency": "AOA",
            "status": "pending",
            "message": "Abra o Multicaixa Express e confirme o pagamento com a referência gerada.",
            "instructions": [
                "Abra o Multicaixa Express no seu telemóvel.",
                "Escolha a opção de pagamento por referência ou transferência, conforme integração disponível.",
                "Use a referência apresentada para concluir o pagamento.",
                "Após a confirmação, o sistema receberá a notificação automática."
            ],
        }

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "order_id": payload.get("order_id"),
            "status": payload.get("status"),
            "reference": payload.get("payment_reference") or payload.get("reference"),
        }


class AppyPayGateway(PaymentGateway):
    """
    Placeholder para futura integração real com AppyPay.
    """

    def create_payment(self, order_id: int, amount: float) -> Dict[str, Any]:
        raise NotImplementedError("AppyPay ainda não configurado")

    def parse_webhook(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "order_id": payload.get("order_id"),
            "status": payload.get("status"),
            "reference": payload.get("payment_reference") or payload.get("reference"),
        }


def get_payment_gateway() -> PaymentGateway:
    """
    Hoje usa mock.
    Futuramente trocar para AppyPayGateway().
    """
    return MockGateway()