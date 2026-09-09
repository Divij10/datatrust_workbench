from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.deps import get_dataset_service
from app.domain.dataset import DatasetMetadata, DatasetProfile
from app.services.dataset_service import DatasetService

router = APIRouter(prefix="/api/v1/datasets", tags=["datasets"])


@router.post("", response_model=DatasetMetadata, status_code=status.HTTP_201_CREATED)
async def upload_dataset(
    file: UploadFile = File(...),
    service: DatasetService = Depends(get_dataset_service),
) -> DatasetMetadata:
    # Read one byte beyond the limit so rejected uploads do not consume unbounded memory.
    content = await file.read(service.max_upload_size_bytes + 1)
    return service.create_dataset(file.filename, content)


@router.get("/{dataset_id}", response_model=DatasetMetadata)
def get_dataset(
    dataset_id: str, service: DatasetService = Depends(get_dataset_service)
) -> DatasetMetadata:
    return service.get_dataset(dataset_id)


@router.get("/{dataset_id}/profile", response_model=DatasetProfile)
def get_dataset_profile(
    dataset_id: str, service: DatasetService = Depends(get_dataset_service)
) -> DatasetProfile:
    return service.get_profile(dataset_id)
