from fastapi import APIRouter

from app.api.v1 import (
    admin,
    auth,
    health,
    home,
    home_admin,
    home_public,
    home_sections_admin,
    orders,
    payments,
    products,
    webhooks,
   
)
from app.api.v1.newsletter import router as newsletter_router
from app.api.v1.newsletter_admin import router as newsletter_admin_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(admin.router)
api_router.include_router(auth.router)
api_router.include_router(products.router)
api_router.include_router(orders.router)
api_router.include_router(webhooks.router)
api_router.include_router(payments.router)
api_router.include_router(health.router)
api_router.include_router(newsletter_router)
api_router.include_router(newsletter_admin_router)
api_router.include_router(home.router)
api_router.include_router(home_admin.router)
api_router.include_router(home_sections_admin.router)
api_router.include_router(home_public.router)