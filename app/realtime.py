from flask import session
from flask_socketio import join_room

from .extensions import socketio


@socketio.on("connect")
def handle_connect():
    user_id = session.get("user_id")
    admin_id = session.get("admin_id")
    if user_id:
        join_room(f"user:{user_id}")
    if admin_id:
        join_room("admins")


@socketio.on("join_order_room")
def join_order_room(data):
    order_id = data.get("order_id")
    if order_id:
        join_room(f"order:{order_id}")
