import io

from fastapi import FastAPI, Form, Request, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader, select_autoescape
from starlette.middleware.sessions import SessionMiddleware

from config import DRIVE_FOLDER_NAME, SECRET_KEY
from app.auth import get_auth_url, exchange_code, get_user_info, creds_to_dict, dict_to_creds
from app.backends.drive_storage import GoogleDriveStorage
from app.backends.memory_store import InMemoryResultStore
from app.services.photo_service import PhotoService
from app.services.result_repository import ResultRepository

app = FastAPI()
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY, max_age=86400)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Starlette Jinja2 래퍼 대신 Jinja2 직접 사용 — 버전 호환성 문제 완전 차단
_jinja = Environment(
    loader=FileSystemLoader("app/templates"),
    autoescape=select_autoescape(["html"]),
)

def _render(template_name: str, **ctx) -> HTMLResponse:
    return HTMLResponse(_jinja.get_template(template_name).render(**ctx))


_store   = InMemoryResultStore()
_results = ResultRepository(_store)

ALLOWED_TYPES   = {"image/jpeg", "image/png", "image/webp", "image/heic"}
VALID_POSITIONS = {"top-left", "top-right", "bottom-left", "bottom-right"}


def _make_service(creds_dict: dict) -> PhotoService:
    creds   = dict_to_creds(creds_dict)
    storage = GoogleDriveStorage(creds, DRIVE_FOLDER_NAME)
    return PhotoService(storage, _store)


# ── 페이지 ──────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return _render("index.html", user=request.session.get("user"))


@app.get("/result/{file_id}", response_class=HTMLResponse)
async def result_page(request: Request, file_id: str):
    data = _results.get(file_id)
    if not data:
        return RedirectResponse("/")

    base_url = str(request.base_url).rstrip("/")
    return _render("result.html",
        user             = request.session.get("user"),
        file_id          = file_id,
        filename         = _results.get_download_filename(file_id),
        drive_url        = data["drive_url"],
        result_image_url = f"{base_url}/preview/{file_id}",
        download_url     = f"{base_url}/download/{file_id}",
        file_size        = data["file_size"],
        qr_position      = data["qr_position"],
    )


# ── 인증 ────────────────────────────────────────────────

@app.get("/auth/login")
async def auth_login(request: Request):
    auth_url, state = get_auth_url()
    request.session["oauth_state"] = state
    return RedirectResponse(auth_url)


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str, state: str):
    if state != request.session.get("oauth_state"):
        raise HTTPException(status_code=400, detail="Invalid OAuth state")

    creds = exchange_code(code)
    user  = get_user_info(creds)

    request.session["credentials"] = creds_to_dict(creds)
    request.session["user"] = {
        "name":    user.get("name"),
        "email":   user.get("email"),
        "picture": user.get("picture"),
    }
    return RedirectResponse("/")


@app.get("/auth/logout")
@app.get("/logout")
async def auth_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/")


# ── 업로드 & 파일 서빙 ───────────────────────────────────

@app.post("/upload")
async def upload(
    request:     Request,
    photo:       UploadFile = File(...),
    qr_position: str        = Form("bottom-right"),
):
    creds_dict = request.session.get("credentials")
    if not creds_dict:
        return RedirectResponse("/", status_code=303)

    if photo.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail="지원하지 않는 파일 형식입니다.")

    if qr_position not in VALID_POSITIONS:
        qr_position = "bottom-right"

    file_bytes = await photo.read()
    filename   = photo.filename or "photo.jpg"

    file_id = _make_service(creds_dict).process(file_bytes, filename, qr_position)
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
