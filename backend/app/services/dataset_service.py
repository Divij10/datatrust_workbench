import io
import json
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

import pandas as pd

from app.adapters.repositories.memory import InMemoryDatasetRepository, StoredDataset
from app.core.config import Settings
from app.core.errors import DomainError
from app.domain.dataset import DatasetDetail, DatasetMetadata, DatasetProfile
from app.services.profiler import DatasetProfiler


class DatasetService:
    def __init__(
        self,
        repository: InMemoryDatasetRepository,
        profiler: DatasetProfiler,
        settings: Settings,
    ) -> None:
        self._repository = repository
        self._profiler = profiler
        self._settings = settings

    @property
    def max_upload_size_bytes(self) -> int:
        """Expose the configured bound so the transport layer can read safely in chunks."""
        return self._settings.max_upload_size_bytes

    def create_dataset(self, filename: str | None, content: bytes) -> DatasetMetadata:
        safe_name, file_type = self._validate_upload(filename, content)
        frame = self._parse(file_type, content)
        if len(frame.index) > self._settings.max_rows:
            raise DomainError(
                "ROW_LIMIT_EXCEEDED",
                "The dataset exceeds the configured row limit.",
                413,
                {"max_rows": self._settings.max_rows},
            )
        profile = self._profiler.profile(frame)
        detail = DatasetDetail(
            id=str(uuid.uuid4()),
            filename=safe_name,
            file_type=file_type,
            size_bytes=len(content),
            created_at=datetime.now(UTC),
            row_count=profile.row_count,
            column_count=profile.column_count,
            profile=profile,
        )
        self._repository.add(StoredDataset(detail=detail, frame=frame))
        return DatasetMetadata.model_validate(detail.model_dump(exclude={"profile"}))

    def get_dataset(self, dataset_id: str) -> DatasetMetadata:
        return self._repository.metadata(dataset_id)

    def get_profile(self, dataset_id: str) -> DatasetProfile:
        return self._repository.get(dataset_id).detail.profile

    def _validate_upload(
        self, filename: str | None, content: bytes
    ) -> tuple[str, Literal["csv", "json"]]:
        if not filename:
            raise DomainError("MISSING_FILENAME", "A filename is required.", 400)
        safe_name = Path(filename).name
        extension = Path(safe_name).suffix.lower()
        if extension not in {".csv", ".json"}:
            raise DomainError(
                "UNSUPPORTED_MEDIA_TYPE",
                "Only .csv and .json datasets are supported.",
                415,
                {"filename": safe_name},
            )
        if not content:
            raise DomainError("EMPTY_UPLOAD", "The uploaded file is empty.", 400)
        if len(content) > self._settings.max_upload_size_bytes:
            raise DomainError(
                "FILE_TOO_LARGE",
                "The uploaded file exceeds the configured size limit.",
                413,
                {"max_size_bytes": self._settings.max_upload_size_bytes},
            )
        return safe_name, "csv" if extension == ".csv" else "json"

    @staticmethod
    def _parse(file_type: Literal["csv", "json"], content: bytes) -> pd.DataFrame:
        try:
            if file_type == "csv":
                frame = pd.read_csv(io.BytesIO(content))
            else:
                decoded = json.loads(content.decode("utf-8"))
                if not isinstance(decoded, list) or not all(
                    isinstance(row, dict) for row in decoded
                ):
                    raise ValueError("JSON must be an array of objects")
                frame = pd.DataFrame(decoded)
        except (
            UnicodeDecodeError,
            ValueError,
            pd.errors.EmptyDataError,
            pd.errors.ParserError,
        ) as error:
            raise DomainError(
                "MALFORMED_DATASET",
                "The uploaded file could not be parsed as a tabular dataset.",
                400,
                {"reason": str(error)},
            ) from error
        if frame.columns.empty:
            raise DomainError("EMPTY_DATASET", "The dataset must contain at least one column.", 400)
        if frame.empty:
            raise DomainError("EMPTY_DATASET", "The dataset must contain at least one row.", 400)
        duplicate_names = frame.columns[frame.columns.duplicated()].tolist()
        if duplicate_names:
            raise DomainError(
                "DUPLICATE_COLUMNS",
                "Column names must be unique.",
                400,
                {"columns": [str(column) for column in duplicate_names]},
            )
        frame.columns = [str(column) for column in frame.columns]
        return frame
