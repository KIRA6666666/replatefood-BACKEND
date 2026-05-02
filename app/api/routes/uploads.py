import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, status

from app.api.deps import CurrentUser

UPLOAD_DIR = Path(__file__).resolve().parents[3] / "static" / "uploads"
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
MAX_SIZE = 5 * 1024 * 1024  # 5 MB

router = APIRouter(prefix="/uploads", tags=["uploads"])


@router.post("/image", status_code=status.HTTP_201_CREATED)
async def upload_image(file: UploadFile, _: CurrentUser) -> dict[str, str]:
    if file.content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Only JPEG, PNG, WebP and GIF images are accepted",
        )

    data = await file.read()
    if len(data) > MAX_SIZE:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="Image must be smaller than 5 MB",
        )

    ext = (file.filename or "image").rsplit(".", 1)[-1].lower()
    if ext not in ("jpg", "jpeg", "png", "webp", "gif"):
        ext = "jpg"

    filename = f"{uuid.uuid4().hex}.{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    (UPLOAD_DIR / filename).write_bytes(data)

    return {"url": f"/static/uploads/{filename}"}
