from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import requests

from openhands.core.config.artifactory_config import ArtifactoryRepositoryType


ARTIFACTORY_API_TIMEOUT = 10.0


class ArtifactoryAPIError(RuntimeError):
    """Raised when calls to the Artifactory API fail."""


@dataclass(slots=True)
class ArtifactoryClient:
    """Simple HTTP client for querying the Artifactory REST API."""

    host: str
    api_key: str
    timeout: float = ARTIFACTORY_API_TIMEOUT

    def _request(
        self, path: str, params: dict[str, str] | None = None
    ) -> requests.Response:
        url = f'{self.host.rstrip('/')}{path}'
        headers = {
            'Accept': 'application/json',
            'X-JFrog-Art-Api': self.api_key,
        }

        try:
            response = requests.get(
                url, headers=headers, params=params, timeout=self.timeout
            )
        except requests.RequestException as exc:  # pragma: no cover - network failure handling
            raise ArtifactoryAPIError(str(exc)) from exc

        if response.status_code >= 400:
            raise ArtifactoryAPIError(
                f'Artifactory API responded with status {response.status_code}'
            )
        return response

    @staticmethod
    def _extract_package_types(payload: object) -> Iterable[str]:
        if not isinstance(payload, list):
            return []

        package_types: set[str] = set()
        for item in payload:
            if not isinstance(item, dict):
                continue

            package_type: str | None = None
            for key in ('packageType', 'repositoryType', 'repoType', 'type', 'key'):
                raw_value = item.get(key)
                if isinstance(raw_value, str) and raw_value.strip():
                    package_type = raw_value.strip().lower()
                    break

            if package_type:
                package_types.add(package_type)

        return package_types

    @staticmethod
    def _extract_repository_names(payload: object) -> list[str]:
        if not isinstance(payload, dict):
            return []

        results = payload.get('results')
        if not isinstance(results, list):
            return []

        names: list[str] = []
        for item in results:
            if not isinstance(item, dict):
                continue
            repo_name = item.get('repo') or item.get('repository') or item.get('key')
            if isinstance(repo_name, str):
                repo_name = repo_name.strip()
                if repo_name and repo_name not in names:
                    names.append(repo_name)
        return names

    def list_supported_repository_types(self) -> list[ArtifactoryRepositoryType]:
        """Return the supported repository types filtered by known package types."""

        response = self._request('/api/repositories/types')
        try:
            payload = response.json()
        except ValueError as exc:
            raise ArtifactoryAPIError('Invalid JSON response from Artifactory') from exc

        package_types = self._extract_package_types(payload)
        supported: list[ArtifactoryRepositoryType] = []
        for repo_type in ArtifactoryRepositoryType:
            if repo_type.value in package_types:
                supported.append(repo_type)
        return supported

    def search_repositories(
        self,
        query: str,
        repository_type: ArtifactoryRepositoryType | str | None = None,
        limit: int = 20,
    ) -> list[str]:
        """Search Artifactory repositories by name using the REST API."""

        normalized_query = query.strip()
        if not normalized_query:
            return []

        repo_type: ArtifactoryRepositoryType | None = None
        if repository_type is not None:
            repo_type = ArtifactoryRepositoryType.from_string(repository_type)

        params: dict[str, str] = {
            'name': f'*{normalized_query}*',
        }
        if repo_type is not None:
            params['packageType'] = repo_type.value

        response = self._request('/api/search/repositories', params=params)
        try:
            payload = response.json()
        except ValueError as exc:
            raise ArtifactoryAPIError('Invalid JSON response from Artifactory') from exc

        names = self._extract_repository_names(payload)
        if limit > 0:
            return names[:limit]
        return names
