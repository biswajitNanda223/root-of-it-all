"""Form data, file uploads (bytes / UploadFile / lists) and mixed bodies."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, File, Form, UploadFile

from app.playground.models import ContactForm
from rio_native import fnv1a64

router = APIRouter(prefix="/forms", tags=["playground: forms & files"])


@router.post("/login", summary="Form fields (application/x-www-form-urlencoded)")
async def login(
    username: Annotated[str, Form()], password: Annotated[str, Form()]
) -> dict[str, str]:
    return {"username": username, "password_length": str(len(password))}


@router.post("/contact", summary="Form *model*")
async def contact(form: Annotated[ContactForm, Form()]) -> ContactForm:
    return form


@router.post("/bytes", summary="`bytes` file: whole file in memory (small files only)")
async def file_bytes(file: Annotated[bytes, File()]) -> dict[str, int]:
    return {"size": len(file), "fnv1a64": fnv1a64(file)}


@router.post("/upload", summary="`UploadFile` + form field in the same request")
async def upload(file: UploadFile, description: Annotated[str, Form()] = "") -> dict[str, object]:
    data = await file.read()
    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": len(data),
        "fnv1a64": fnv1a64(data),
        "description": description,
    }


@router.post("/multi", summary="Multiple files")
async def multi(
    files: Annotated[list[UploadFile], File(description="One or more files")],
) -> dict[str, list[str | None]]:
    return {"filenames": [f.filename for f in files]}
