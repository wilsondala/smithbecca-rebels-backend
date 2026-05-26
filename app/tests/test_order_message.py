from app.services.order_message import build_order_message


class FakeProduct:
    def __init__(self, name):
        self.name = name


class FakeItem:
    def __init__(self, product, quantity, price):
        self.product = product
        self.quantity = quantity
        self.price = price


class FakeUser:
    def __init__(self, name):
        self.name = name


class FakeOrder:
    def __init__(self):
        self.id = 1
        self.user = FakeUser("Wilsondala")
        self.payment_method = "Entrega"
        self.items = [
            FakeItem(FakeProduct("Batom Vermelho"), 2, 2000),
            FakeItem(FakeProduct("Perfume Luxo"), 1, 8000),
        ]
        self.total = 12000


def test_build_order_message():
    order = FakeOrder()

    message = build_order_message(order)

    assert "NOVO PEDIDO" in message
    assert "Wilsondala" in message
    assert "Batom Vermelho" in message
    assert "Perfume Luxo" in message
    assert "Total" in message
    assert "12" in message
    assert "Kz" in message

    assert "Entrega" in message
