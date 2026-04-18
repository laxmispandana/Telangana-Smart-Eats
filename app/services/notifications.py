from ..extensions import socketio
from .orders import serialize_order_socket_payload


def emit_cart_update(user_id, cart_meta):
    socketio.emit(
        "cart_updated",
        {
            "count": cart_meta["count"],
            "total": cart_meta["total"],
        },
        to=f"user:{user_id}",
    )


def emit_order_update(order, message=None):
    payload = serialize_order_socket_payload(order)
    if message:
        payload["message"] = message
    socketio.emit("order_status_updated", payload, to=f"order:{order.id}")
    socketio.emit("order_status_updated", payload, to=f"user:{order.user_id}")
    socketio.emit("admin_order_updated", payload, to="admins")


def emit_toast(room, title, body, level="info"):
    socketio.emit(
        "toast",
        {"title": title, "body": body, "level": level},
        to=room,
    )
