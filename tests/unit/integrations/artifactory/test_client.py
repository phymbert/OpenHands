from __future__ import annotations

import pytest

from openhands.core.config.artifactory_config import ArtifactoryRepositoryType
from openhands.integrations.artifactory.client import (
    ArtifactoryAPIError,
    ArtifactoryClient,
)


class _DummyResponse:
    def __init__(self, payload: object) -> None:
        self._payload = payload

    def json(self) -> object:
        return self._payload


def test_extract_repository_names_parses_results() -> None:
    payload = {
        'results': [
            {'repo': ' libs-release '},
            {'repository': 'docker-local'},
            {'key': 'nuget-local'},
            {'repo': ''},
            {'repo': None},
            'invalid',
        ]
    }

    names = ArtifactoryClient._extract_repository_names(payload)
    assert names == ['libs-release', 'docker-local', 'nuget-local']


def test_search_repositories_builds_request(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, dict[str, str] | None] = {}

    client = ArtifactoryClient(host='https://example.jfrog.io', api_key='token')

    def fake_request(
        self: ArtifactoryClient, path: str, params: dict[str, str] | None = None
    ):
        captured[path] = params
        return _DummyResponse(
            {
                'results': [
                    {'repo': 'libs-release'},
                    {'repo': 'libs-snapshot'},
                    {'repo': 'docker-local'},
                ]
            }
        )

    monkeypatch.setattr(ArtifactoryClient, '_request', fake_request)

    names = client.search_repositories('libs', ArtifactoryRepositoryType.PYPI, limit=2)

    assert names == ['libs-release', 'libs-snapshot']
    assert '/api/search/repositories' in captured
    params = captured['/api/search/repositories']
    assert params is not None
    assert params['name'] == '*libs*'
    assert params['packageType'] == ArtifactoryRepositoryType.PYPI.value


def test_search_repositories_raises_on_invalid_json(monkeypatch: pytest.MonkeyPatch) -> None:
    client = ArtifactoryClient(host='https://example.jfrog.io', api_key='token')

    class _BadResponse:
        def json(self) -> object:
            raise ValueError('no json')

    monkeypatch.setattr(
        ArtifactoryClient,
        '_request',
        lambda self, *args, **kwargs: _BadResponse(),
    )

    with pytest.raises(ArtifactoryAPIError):
        client.search_repositories('example')


def test_search_repositories_returns_empty_for_blank_query() -> None:
    client = ArtifactoryClient(host='https://example.jfrog.io', api_key='token')
    assert client.search_repositories('   ') == []
    assert client.search_repositories('') == []
