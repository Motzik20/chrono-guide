from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("/image")
async def ingest_image(image: UploadFile = File(...)) -> dict[str, str]:
    content_type: str | None = image.content_type
    if content_type is None:
        raise HTTPException(status_code=400, detail="No valid image content type")
    if content_type not in ["image/jpeg", "image/png", "application/pdf"]:
        raise HTTPException(status_code=400, detail="Invalid image content type")
    return {"Not implemented": "Ingesting images is not implemented"}
