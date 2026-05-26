from app.database.session import engine
from app.database.base import Base

# Importa models para registrar no metadata
from app.models.user import User
from app.models.product import Product
from app.models.order import Order
from app.models.order_item import OrderItem


def init():
    print("Criando tabelas...")
    Base.metadata.create_all(bind=engine)
    print("Concluído.")


if __name__ == "__main__":
    init()