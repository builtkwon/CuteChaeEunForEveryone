import io
import qrcode
from PIL import Image, UnidentifiedImageError

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

_SIZE_RATIO    = 0.18
_MARGIN        = 20               # 좌상단 여백 (px)
_MAX_DIMENSION = 4096
_TARGET_BYTES  = 10 * 1024 * 1024
_QUALITY_STEPS = [90, 80, 70, 60]

# 모자이크 QR 명암 계수 — 스캔 우선
_DARK_FACTOR  = 0.35   # 검정 모듈: 사진 색상의 35% → 어둡고 색감 유지
_LIGHT_BASE   = 217    # 흰색 모듈: 255 × 0.85 (밝은 베이스)
_LIGHT_FACTOR = 0.15   # 흰색 모듈: 사진 색상의 15% 혼합


def validate_image(image_bytes: bytes) -> None:
    """실제 이미지 파일인지 Pillow로 검증합니다."""
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except (UnidentifiedImageError, Exception) as e:
        raise ValueError(f"유효하지 않은 이미지 파일입니다: {e}") from e


def compress_if_needed(image_bytes: bytes) -> bytes:
    """이미지가 목표 용량을 초과하면 자동 압축합니다."""
    if len(image_bytes) <= _TARGET_BYTES:
        return image_bytes

    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size

    if max(w, h) > _MAX_DIMENSION:
        ratio = _MAX_DIMENSION / max(w, h)
        img   = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    result = image_bytes
    for quality in _QUALITY_STEPS:
        out = io.BytesIO()
        img.convert("RGB").save(out, format="JPEG", quality=quality)
        result = out.getvalue()
        if len(result) <= _TARGET_BYTES:
            break

    return result


def _make_mosaic_qr(photo_region: Image.Image, url: str, size: int) -> Image.Image:
    """사진 색상이 스며든 모자이크 QR 코드를 생성합니다.

    - quiet zone(흰색 테두리) 제거 (border=0)
    - 검정 모듈: 사진 픽셀 × _DARK_FACTOR  → 어둡지만 색감 유지
    - 흰색 모듈: 사진 픽셀 × _LIGHT_FACTOR + 흰색 × 0.85 → 밝지만 살짝 물듦
    - NEAREST 리사이즈로 모듈 경계 선명하게 유지 (스캔 정확도 보장)
    """
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=0,
    )
    qr.add_data(url)
    qr.make(fit=True)

    qr_mask = qr.make_image(fill_color="black", back_color="white") \
                .convert("L") \
                .resize((size, size), Image.NEAREST)

    region = photo_region.resize((size, size), Image.LANCZOS).convert("RGB")

    dark  = region.point(lambda x: int(x * _DARK_FACTOR))
    light = region.point(lambda x: int(x * _LIGHT_FACTOR + _LIGHT_BASE))

    # qr_mask: 흰 모듈=255 → light, 검정 모듈=0 → dark
    return Image.composite(light, dark, qr_mask)


def compose(image_bytes: bytes, download_url: str) -> bytes:
    """QR 코드를 사진 좌상단에 모자이크 방식으로 합성합니다."""
    photo   = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    pw, ph  = photo.size
    qr_size = int(min(pw, ph) * _SIZE_RATIO)
    x0, y0  = _MARGIN, _MARGIN

    photo_region = photo.crop((x0, y0, x0 + qr_size, y0 + qr_size))
    qr_overlay   = _make_mosaic_qr(photo_region, download_url, qr_size)

    photo.paste(qr_overlay, (x0, y0))

    out = io.BytesIO()
    photo.save(out, format="JPEG", quality=95)
    return out.getvalue()
