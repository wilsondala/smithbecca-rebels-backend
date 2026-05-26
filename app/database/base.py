from app.database.base_class import Base

from app.models.user import User
from app.models.product import Product
from app.models.review import Review  # 🔥 ESSA LINHA É O FIX
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.home_banner import HomeBanner
from app.models.home_section import HomeSection

# se existir no seu projeto, mantenha também:
# from app.models.newsletter import NewsletterSubscriber

# se existir no seu projeto, mantenha também:
# from app.models.newsletter import NewsletterSubscriber
# from app.models.review import Review