import io
import qrcode
from PIL import Image, UnidentifiedImageError

try:
    from pillow_heif import register_heif_opener
    register_heif_opener()
except ImportError:
    pass

_SIZE_RATIO    = 0.15
_MARGIN        = 20
_PADDING       = 10
_MAX_DIMENSION = 4096              # 이 픽셀 초과 시 축소
_TARGET_BYTES  = 10 * 1024 * 1024  # 압축 목표 용량 (10MB)
_QUALITY_STEPS = [90, 80, 70, 60]  # 단계적 품질 감소


def validate_image(image_bytes: bytes) -> None:
    """실제 이미지 파일인지 Pillow로 검증합니다.

    Content-Type 헤더 위조로 악성 파일이 통과하는 것을 차단합니다.
    유효하지 않으면 ValueError를 발생시킵니다.
    """
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()
    except (UnidentifiedImageError, Exception) as e:
        raise ValueError(f"유효하지 않은 이미지 파일입니다: {e}") from e


def compress_if_needed(image_bytes: bytes) -> bytes:
    """이미지가 목표 용량을 초과하면 자동 압축합니다.

    1단계: 해상도가 _MAX_DIMENSION 초과 시 비율 유지하며 축소
    2단계: JPEG 품질을 단계적으로 낮춰 _TARGET_BYTES 이하로 조정
    목표 용량 이하면 원본 그대로 반환합니다.
    """
    if len(image_bytes) <= _TARGET_BYTES:
        return image_bytes

    img = Image.open(io.BytesIO(image_bytes))
    w, h = img.size

    # 1단계: 해상도 축소
    if max(w, h) > _MAX_DIMENSION:
        ratio = _MAX_DIMENSION / max(w, h)
        img   = img.resize((int(w * ratio), int(h * ratio)), Image.LANCZOS)

    # 2단계: 품질 단계 감소
    result = image_bytes
    for quality in _QUALITY_STEPS:
        out = io.BytesIO()
        img.convert("RGB").save(out, format="JPEG", quality=quality)
        result = out.getvalue()
        if len(result) <= _TARGET_BYTES:
            break

    return result


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
