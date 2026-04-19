import base64
import uuid
from io import BytesIO
from urllib.parse import urlencode

import qrcode
import qrcode.image.svg


def build_upi_payload(upi_id, amount):
    params = {
        "pa": upi_id,
        "pn": "FoodSprint",
        "am": f"{amount:.2f}",
        "cu": "INR",
    }
    return f"upi://pay?{urlencode(params)}"


def generate_qr_data_uri(payload):
    image = qrcode.make(payload, image_factory=qrcode.image.svg.SvgImage)
    buffer = BytesIO()
    image.save(buffer)
    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")
    return f"data:image/svg+xml;base64,{encoded}"


def fake_transaction_id():
    return f"UPI-{uuid.uuid4().hex[:10].upper()}"
