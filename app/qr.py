import qrcode
from io import BytesIO


def generate_qr_png(data: str) -> bytes:
    qr = qrcode.make(data)

    buffer = BytesIO()
    qr.save(buffer, format="PNG")

    return buffer.getvalue()