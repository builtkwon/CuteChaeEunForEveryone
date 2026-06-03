import io

from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape

from config import (
    R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY,
    R2_BUCKET_NAME, R2_PUBLIC_URL,
)
from app.backends.r2_storage import CloudflareR2Storage
from app.backends.memory_store import InMemoryResultStore
from app.services.photo_service import PhotoService
from app.services.result_repository import ResultRepository

app = FastAPI()
app.mount("/static", StaticFiles(directory="app/static"), name="static")

_jinja = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html"]),
)

def _render(template_name: str, **ctx) -> HTMLResponse:
    return HTMLResponse(_jinja.get_template(template_name).render(**ctx))


# 앱 시작 시 한 번만 생성 — 인증 불필요
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
async def result_page(request: Request, file_id: str):
    data = _results.get(file_id)
    if not data:
        return RedirectResponse("/")

    base_url = str(request.base_url).rstrip("/")
    return _render("result.html",
        file_id          = file_id,
        filename         = _results.get_download_filename(file_id),
        drive_url        = data["drive_url"],
        result_image_url = f"{base_url}/preview/{file_id}",
        download_url     = f"{base_url}/download/{file_id}",
        file_size        = data["file_size"],
        qr_position      = data["qr_position"],
    )


# ── 업로드 & 파일 서빙 ───────────────────────────────────

@app.post("/upload")
async def upload(
    request:     Request,
    photo:       UploadFile = File(...),
    qr_position: str        = Form("bottom-right"),
):
    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    if qr_position not in VALID_POSITIONS:
        qr_position = "bottom-right"

    file_bytes = await photo.read()
    filename   = photo.filename or "photo.jpg"

    file_id = _service.process(file_bytes, filename, qr_position)
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

    return StreamingResponse(
        io.BytesIO(data["data"]),
        media_type="image/jpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
