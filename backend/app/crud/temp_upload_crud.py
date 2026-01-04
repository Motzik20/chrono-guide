from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models.temp_upload import TempUpload


def get_upload_record(upload_id: int, session: Session) -> TempUpload:
    record = session.exec(select(TempUpload).where(TempUpload.id == upload_id)).first()
    if not record:
        raise NotFoundError(f"Upload record for id {upload_id} not found")
    return record


def create_upload_record(upload: TempUpload, session: Session) -> TempUpload:
    session.add(upload)
    session.flush()
    session.refresh(upload)
    return upload


def delete_upload_record(upload: TempUpload, session: Session) -> None:
    session.delete(upload)
    session.flush()
