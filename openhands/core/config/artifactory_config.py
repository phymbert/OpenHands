from __future__ import annotations

from enum import Enum
from typing import Dict

import shlex

from pydantic import BaseModel, ConfigDict, Field, SecretStr


class ArtifactoryRepositoryType(str, Enum):
    """Supported repository types for JFrog Artifactory configuration."""

    PYTHON = 'python'
    JAVASCRIPT = 'javascript'
    JAVA = 'java'
    GO = 'go'


DEFAULT_ARTIFACTORY_SERVER_ID = 'openhands-artifactory'


class ArtifactoryConfig(BaseModel):
    """Configuration for connecting package managers to JFrog Artifactory."""

    host: str | None = Field(default=None, description='Base URL for Artifactory')
    api_key: SecretStr | None = Field(default=None, description='Artifactory API key')
    repositories: dict[ArtifactoryRepositoryType, str] = Field(
        default_factory=dict,
        description='Mapping of repository types to Artifactory repository keys',
    )
    server_id: str = Field(
        default=DEFAULT_ARTIFACTORY_SERVER_ID,
        description='Identifier used when configuring jfrog CLI',
    )

    model_config = ConfigDict(use_enum_values=True)

    def is_configured(self) -> bool:
        """Return True when Artifactory integration has enough data to run."""

        return bool(self.host and self.api_key)

    def normalized_host(self) -> str | None:
        """Return the Artifactory host without a trailing slash."""

        if not self.host:
            return None
        return self.host.rstrip('/')

    def api_key_value(self) -> str | None:
        if not self.api_key:
            return None
        return self.api_key.get_secret_value()

    def repository_commands(self) -> Dict[ArtifactoryRepositoryType, str]:
        """Return jfrog CLI configuration commands per repository type."""

        commands: dict[ArtifactoryRepositoryType, str] = {}

        for repo_type, repo_key in self.repositories.items():
            normalized_repo = repo_key.strip()
            if not normalized_repo:
                continue

            repo_arg = shlex.quote(normalized_repo)
            server_arg = shlex.quote(self.server_id)

            if repo_type == ArtifactoryRepositoryType.PYTHON:
                commands[repo_type] = (
                    f'jfrog pip-config --server-id-resolve {server_arg} '
                    f'--repo-resolve {repo_arg} --interactive=false'
                )
            elif repo_type == ArtifactoryRepositoryType.JAVASCRIPT:
                commands[repo_type] = (
                    f'jfrog npm-config --server-id-resolve {server_arg} '
                    f'--repo-resolve {repo_arg} --interactive=false'
                )
            elif repo_type == ArtifactoryRepositoryType.JAVA:
                commands[repo_type] = (
                    f'jfrog mvn-config --server-id-resolve {server_arg} '
                    f'--repo-resolve {repo_arg} --interactive=false'
                )
            elif repo_type == ArtifactoryRepositoryType.GO:
                commands[repo_type] = (
                    f'jfrog go-config --server-id-resolve {server_arg} '
                    f'--repo-resolve {repo_arg} --interactive=false'
                )

        return commands

