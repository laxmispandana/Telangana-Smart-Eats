from ..extensions import db
from ..models import Order, OrderItem, OrderStatusEvent, PaymentTransaction


ORDER_STATUS_FLOW = ["Placed", "Preparing", "Out for Delivery", "Delivered"]
PAYMENT_STATUS_FLOW = ["pending", "verification_pending", "paid", "failed"]


def append_order_status(order, status, note=None):
    event = OrderStatusEvent(order_id=order.id, status=status, note=note)
    order.status = status
    db.session.add(event)
    return event


def create_order_with_items(user_id, cart_meta, status="Placed", payment_status="pending"):
    order = Order(
        user_id=user_id,
        total_amount=cart_meta["total"],
        payment_status=payment_status,
        status=status,
    )
    db.session.add(order)
    db.session.flush()

    for item in cart_meta["entries"]:
        db.session.add(
            OrderItem(
                order_id=order.id,
                menu_item_id=item["menu_item"].id,
                quantity=item["quantity"],
                price=item["menu_item"].price,
            )
        )

    append_order_status(order, status, note="Order created")
    return order


def create_payment_record(
    order,
    *,
    provider,
    method,
    amount,
    status="pending",
    transaction_id=None,
    gateway_order_id=None,
    gateway_payment_id=None,
    gateway_signature=None,
    upi_id=None,
    qr_payload=None,
    metadata_json=None,
):
    payment = PaymentTransaction(
        order_id=order.id,
        provider=provider,
        method=method,
        status=status,
        amount=amount,
        transaction_id=transaction_id,
        gateway_order_id=gateway_order_id,
        gateway_payment_id=gateway_payment_id,
        gateway_signature=gateway_signature,
        upi_id=upi_id,
        qr_payload=qr_payload,
        metadata_json=metadata_json,
    )
    db.session.add(payment)
    return payment


def serialize_order_timeline(order):
    return [
        {
            "status": event.status,
            "note": event.note,
            "created_at": event.created_at.strftime("%d %b %Y, %I:%M %p"),
        }
        for event in order.status_events
    ]


def serialize_order_socket_payload(order):
    latest_payment = order.latest_payment
    return {
        "order_id": order.id,
        "status": order.status,
        "payment_status": order.payment_status,
        "payment_method": latest_payment.method if latest_payment else "Unknown",
        "timeline": serialize_order_timeline(order),
    }
