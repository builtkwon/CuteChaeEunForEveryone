import io
from urllib.parse import quote

from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.middleware.base import BaseHTTPMiddleware

from config import (
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME, R2_PUBLIC_URL,
)
from app.backends.r2_storage import CloudflareR2Storage
from app.backends.memory_store import InMemoryResultStore
from app.services.photo_service import PhotoService
from app.services.result_repository import ResultRepository
from app.qr_composer import validate_image

MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB (압축 전 원본 기준, ProRAW 등 고려)

app = FastAPI()


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"]        = "DENY"
        response.headers["Referrer-Policy"]        = "strict-origin-when-cross-origin"
        return response


app.add_middleware(SecurityHeadersMiddleware)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

_jinja = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html"]),
)

def _render(template_name: str, **ctx) -> HTMLResponse:
    return HTMLResponse(_jinja.get_template(template_name).render(**ctx))


_storage = CloudflareR2Storage(
    account_id        = R2_ACCOUNT_ID,
    access_key_id     = R2_ACCESS_KEY_ID,
    secret_access_key = R2_SECRET_ACCESS_KEY,
    bucket_name       = R2_BUCKET_NAME,
    public_url        = R2_PUBLIC_URL,
)
_store   = InMemoryResultStore()
_results = ResultRepository(_store)
_service = PhotoService(_storage, _store)

ALLOWED_TYPES   = {"image/jpeg", "image/png", "image/webp", "image/heic"}
VALID_POSITIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}


# ── 페이지 ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index():
    return _render("index.html")


@app.get("/result/{file_id}", response_class=HTMLResponse)
async def result_page(file_id: str):
    data = _results.get(file_id)
    if not data:
        return RedirectResponse("/")

    return _render("result.html",
        file_id          = file_id,
        filename         = _results.get_download_filename(file_id),
        drive_url        = data["drive_url"],
        result_image_url = f"/preview/{file_id}",
        download_url     = f"/download/{file_id}",
        file_size        = data["file_size"],
        qr_position      = data["qr_position"],
    )


# ── 업로드 & 파일 서빙 ───────────────────────────────────

@app.post("/upload")
async def upload(
    photo:       UploadFile = File(...),
    qr_position: str        = Form("top-left"),
):
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    if qr_position not in VALID_POSITIONS:
        qr_position = "top-left"

    file_bytes = await photo.read()

    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="파일 크기는 최대 50MB까지 허용됩니다.")

    try:
        validate_image(file_bytes)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    filename = photo.filename or "photo.jpg"
    file_id  = _service.process(file_bytes, filename, qr_position)
    return RedirectResponse(f"/result/{file_id}", status_code=303)


@app.get("/preview/{file_id}")
async def preview(file_id: str):
    data = _results.get(file_id)
    if not data:
        raise HTTPException(status_code=404)
    return StreamingResponse(io.BytesIO(data["data"]), media_type="image/jpeg")


@app.get("/download/{file_id}")
async def download(file_id: str):
    data     = _results.get(file_id)
    filename = _results.get_download_filename(file_id)
    if not data or not filename:
        raise HTTPException(status_code=404)

    # RFC 5987 인코딩으로 파일명 특수문자 안전 처리
    encoded = quote(filename, safe="")
    return StreamingResponse(
        io.BytesIO(data["data"]),
        media_type="image/jpeg",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded}"},
    )
