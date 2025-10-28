from fastapi import APIRouter, UploadFile, File, HTTPException, Request
from fastapi.responses import JSONResponse
from controllers import DataController
from pathlib import Path
from pathvalidate import sanitize_filename
from uuid import uuid4

data_router = APIRouter(
    prefix="/data",
    tags=["Data Operations"],
)

@data_router.post("/upload/{project_id}")
async def upload_data(request: Request, project_id: str, file: UploadFile = File(...)):
    data_controller = DataController()
    try:
        data_controller.validate_content_type(file)
        data_controller.validate_project_id(project_id)
        data_controller.validate_file_size(file)

        safe_name = sanitize_filename(file.filename).lower()

        BASE_DIR =data_controller.BASE_DIR
        target_dir = BASE_DIR / "assets" / project_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / safe_name

        if file_path.exists():
            existing_hash = data_controller.file_hash(file_path.read_bytes())
            file.file.seek(0)
            new_hash = data_controller.file_hash(await file.read())
            if existing_hash == new_hash:
                raise HTTPException(status_code=400, detail="A file with the same name and content already exists.")
            else:
                if "." in safe_name:
                    name, ext = safe_name.rsplit(".", 1)
                    safe_name = f"{name}_{uuid4().hex[:8]}.{ext}"
                else:
                    safe_name = f"{safe_name}_{uuid4().hex[:8]}"
                file_path = target_dir / safe_name

        with open(file_path, "wb") as f:
            while chunk := file.file.read(1024):
                f.write(chunk)

        return JSONResponse(
            status_code=200,
            content={
                "signal": "Success",
                "file_name": safe_name,
                "saved_to": str(file_path)
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"signal": "Error", "message": str(e)}
        )