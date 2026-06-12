import os
from fastapi import APIRouter, UploadFile, File, Depends
from sqlalchemy.orm import Session
from app.database import get_session, KnowledgeFile
from app.ingest.pipeline import ingest_file, ingest_all

router = APIRouter(prefix="/api/portal", tags=["portal"])


@router.post("/upload")
def upload_knowledge(file: UploadFile = File(...), db: Session = Depends(get_session)):
    if not file.filename.endswith((".md", ".txt")):
        return {"error": "仅支持 .md 和 .txt 文件"}
    content = file.file.read()
    tmp_path = f"/tmp/{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(content)
    result = ingest_file(tmp_path, db)
    os.remove(tmp_path)
    return result


@router.get("/files")
def list_files(db: Session = Depends(get_session)):
    files = db.query(KnowledgeFile).order_by(KnowledgeFile.imported_at.desc()).all()
    return [
        {
            "id": f.id,
            "filename": f.filename,
            "chunk_count": f.chunk_count,
            "file_size": f.file_size,
            "imported_at": f.imported_at.isoformat() if f.imported_at else "",
        }
        for f in files
    ]


@router.delete("/files/{file_id}")
def delete_file(file_id: int, db: Session = Depends(get_session)):
    kf = db.query(KnowledgeFile).filter_by(id=file_id).first()
    if not kf:
        return {"error": "文件不存在"}
    filepath = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "knowledge", kf.filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    db.delete(kf)
    db.commit()
    from app.ingest.pipeline import _rebuild_vector_store
    _rebuild_vector_store()
    return {"message": f"{kf.filename} 已删除"}


@router.post("/reimport")
def reimport_all(db: Session = Depends(get_session)):
    results = ingest_all(db)
    return {"results": results}
