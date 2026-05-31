import io
import qrcode
from PIL import Image

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass  # HEIC 미지원 환경에서도 동작

_SIZE_RATIO = 0.15   # 사진 짧은 변 대비 QR 크기 비율
_MARGIN     = 20     # 가장자리 여백 (px)
_PADDING    = 10     # QR 흰 배경 내부 여백 (px)


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


def _add_white_padding(img: Image.Image, padding: int = _PADDING) -> Image.Image:
    w, h = img.size
    bg = Image.new("RGBA", (w + padding * 2, h + padding * 2), (255, 255, 255, 220))
    bg.paste(img, (padding, padding))
    return bg


def compose(image_bytes: bytes, download_url: str, qr_position: str) -> bytes:
    photo = Image.open(io.BytesIO(image_bytes)).convert("RGBA")
    pw, ph = photo.size

    qr_size = int(min(pw, ph) * _SIZE_RATIO)
    qr_img  = _add_white_padding(_make_qr(download_url, qr_size))
    qw, qh  = qr_img.size

    positions = {
        "top-left":     (_MARGIN, _MARGIN),
        "top-right":    (pw - qw - _MARGIN, _MARGIN),
        "bottom-left":  (_MARGIN, ph - qh - _MARGIN),
        "bottom-right": (pw - qw - _MARGIN, ph - qh - _MARGIN),
    }
    photo.paste(qr_img, positions.get(qr_position, positions["bottom-right"]), qr_img)

    out = io.BytesIO()
    photo.convert("RGB").save(out, format="JPEG", quality=95)
    return out.getvalue()
