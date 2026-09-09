from collections.abc import Mapping
from typing import Any, Protocol

from app.domain.dataset import DatasetProfile


class RuleGenerator(Protocol):
    """Returns untrusted structured output for one central validation path."""

    async def generate_rules(self, profile: DatasetProfile) -> Mapping[str, Any]: ...
