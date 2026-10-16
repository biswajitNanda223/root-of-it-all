import hashlib

from fastapi import APIRouter, UploadFile

from app.api.deps import CurrentUser, SettingsDep
from app.api.schemas import FileInfo
from rio_core.errors import PayloadTooLargeError

router = APIRouter(prefix="/files", tags=["files"])


@router.post("", response_model=FileInfo, summary="Upload a file (streamed, size-capped)")
async def upload(file: UploadFile, _: CurrentUser, settings: SettingsDep) -> FileInfo:
    digest, size = hashlib.sha256(), 0
    while chunk := await file.read(64 * 1024):
        size += len(chunk)
        if size > settings.max_upload_bytes:
            raise PayloadTooLargeError(f"Limit is {settings.max_upload_bytes} bytes")
        digest.update(chunk)
    return FileInfo(
        filename=file.filename, content_type=file.content_type, size=size, sha256=digest.hexdigest()
    )
