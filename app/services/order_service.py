from app.services.whatsapp_service import send_order_notifications

db.add(order)
db.commit()
db.refresh(order)

try:
    send_order_notifications(order)
except Exception as e:
    print("Erro ao enviar WhatsApp do pedido:", e)