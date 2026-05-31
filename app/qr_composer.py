import io
import qrcode
from PIL import Image
from config import QR_SIZE_RATIO, QR_MARGIN, QR_POSITION

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # HEIC 미지원 환경에서도 동작


def _make_qr(url: str, size: int) -> Image.Image:
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=2,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    return img.resize((size, size), Image.LANCZOS)


def _add_white_padding(img: Image.Image, padding: int = 10) -> Image.Image:
    w, h = img.size
    bg = Image.new("RGBA", (w + padding * 2, h + padding * 2), (255, 255, 255, 220))
    bg.paste(img, (padding, padding))
    return bg


def compose(image_bytes: bytes, download_url: str, qr_position: str = QR_POSITION) -> bytes:
    photo = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    pw, ph = photo.size

    qr_size = int(min(pw, ph) * QR_SIZE_RATIO)
    qr_img = _add_white_padding(_make_qr(download_url, qr_size))
    qw, qh = qr_img.size

    positions = {
        "top-left":     (QR_MARGIN, QR_MARGIN),
        "top-right":    (pw - qw - QR_MARGIN, QR_MARGIN),
        "bottom-left":  (QR_MARGIN, ph - qh - QR_MARGIN),
        "bottom-right": (pw - qw - QR_MARGIN, ph - qh - QR_MARGIN),
    }
    photo.paste(qr_img, positions.get(qr_position, positions["bottom-right"]), qr_img)

    out = io.BytesIO()
    photo.convert("RGB").save(out, format="JPEG", quality=95)
    return out.getvalue()
