from __future__ import annotations

from enum import Enum
from typing import Dict

import shlex

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator


class ArtifactoryRepositoryType(str, Enum):
    """Supported repository types for JFrog Artifactory configuration."""

    PYPI = 'pypi'
    NPM = 'npm'
    MAVEN = 'maven'
    GRADLE = 'gradle'
    GO = 'go'
    NUGET = 'nuget'
    DOCKER = 'docker'
    HELM = 'helm'
    TERRAFORM = 'terraform'
    CONAN = 'conan'
    CARGO = 'cargo'
    COMPOSER = 'composer'
    GEMS = 'gems'
    COCOAPODS = 'cocoapods'
    CRAN = 'cran'
    PUB = 'pub'
    SBT = 'sbt'
    IVY = 'ivy'
    SWIFT = 'swift'
    BOWER = 'bower'

    @classmethod
    def from_string(cls, value: str | 'ArtifactoryRepositoryType') -> 'ArtifactoryRepositoryType | None':
        """Convert arbitrary string input into a supported repository type."""

        if isinstance(value, cls):
            return value

        normalized = str(value).strip().lower()
        if not normalized:
            return None

        try:
            return cls(normalized)
        except ValueError:
            alias = ARTIFACTORY_REPOSITORY_ALIASES.get(normalized)
            if alias:
                return alias
        return None

ARTIFACTORY_REPOSITORY_ALIASES: dict[str, ArtifactoryRepositoryType] = {
    'python': ArtifactoryRepositoryType.PYPI,
    'python-pypi': ArtifactoryRepositoryType.PYPI,
    'pip': ArtifactoryRepositoryType.PYPI,
    'javascript': ArtifactoryRepositoryType.NPM,
    'node': ArtifactoryRepositoryType.NPM,
    'nodejs': ArtifactoryRepositoryType.NPM,
    'yarn': ArtifactoryRepositoryType.NPM,
    'pnpm': ArtifactoryRepositoryType.NPM,
    'java': ArtifactoryRepositoryType.MAVEN,
    'kotlin': ArtifactoryRepositoryType.GRADLE,
    'scala': ArtifactoryRepositoryType.SBT,
    'golang': ArtifactoryRepositoryType.GO,
    'ruby': ArtifactoryRepositoryType.GEMS,
    'rubygems': ArtifactoryRepositoryType.GEMS,
    'php': ArtifactoryRepositoryType.COMPOSER,
    '.net': ArtifactoryRepositoryType.NUGET,
    'dotnet': ArtifactoryRepositoryType.NUGET,
    'csharp': ArtifactoryRepositoryType.NUGET,
    'c#': ArtifactoryRepositoryType.NUGET,
    'rust': ArtifactoryRepositoryType.CARGO,
    'swiftpm': ArtifactoryRepositoryType.SWIFT,
    'ios': ArtifactoryRepositoryType.COCOAPODS,
    'objective-c': ArtifactoryRepositoryType.COCOAPODS,
    'c++': ArtifactoryRepositoryType.CONAN,
    'cpp': ArtifactoryRepositoryType.CONAN,
    'c': ArtifactoryRepositoryType.CONAN,
    'dart': ArtifactoryRepositoryType.PUB,
    'r': ArtifactoryRepositoryType.CRAN,
}


DEFAULT_ARTIFACTORY_SERVER_ID = 'openhands-artifactory'
DEFAULT_JFROG_CLI_INSTALL_URL = 'https://getcli.jfrog.io'


COMMAND_TEMPLATES: Dict[ArtifactoryRepositoryType, str] = {
    ArtifactoryRepositoryType.PYPI: (
        'jfrog pip-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.NPM: (
        'jfrog npm-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.MAVEN: (
        'jfrog mvn-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.GRADLE: (
        'jfrog gradle-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.GO: (
        'jfrog go-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.NUGET: (
        'jfrog nuget-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.DOCKER: (
        'jfrog docker-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.HELM: (
        'jfrog helm-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.TERRAFORM: (
        'jfrog terraform-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.CONAN: (
        'jfrog conan-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.CARGO: (
        'jfrog cargo-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.COMPOSER: (
        'jfrog composer-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.GEMS: (
        'jfrog gem-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.COCOAPODS: (
        'jfrog cocoapods-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.CRAN: (
        'jfrog cran-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.PUB: (
        'jfrog pub-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.SBT: (
        'jfrog sbt-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.IVY: (
        'jfrog ivy-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.SWIFT: (
        'jfrog swift-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
    ArtifactoryRepositoryType.BOWER: (
        'jfrog bower-config --server-id-resolve {server} '
        '--repo-resolve {repo} --interactive=false'
    ),
}


class ArtifactoryConfig(BaseModel):
    """Configuration for connecting package managers to JFrog Artifactory."""

    host: str | None = Field(default=None, description='Base URL for Artifactory')
    api_key: SecretStr | None = Field(default=None, description='Artifactory API key')
    cli_install_url: str | None = Field(
        default=DEFAULT_JFROG_CLI_INSTALL_URL,
        description='URL used to download the jfrog CLI installer',
    )
    repositories: dict[ArtifactoryRepositoryType, str] = Field(
        default_factory=dict,
        description='Mapping of repository types to Artifactory repository keys',
    )
    server_id: str = Field(
        default=DEFAULT_ARTIFACTORY_SERVER_ID,
        description='Identifier used when configuring jfrog CLI',
    )

    model_config = ConfigDict(use_enum_values=True)

    @field_validator('repositories', mode='before')
    @classmethod
    def _normalize_repositories(
        cls, value: dict | None
    ) -> dict[ArtifactoryRepositoryType, str]:
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise ValueError('artifactory repositories must be provided as a mapping')

        normalized: dict[ArtifactoryRepositoryType, str] = {}
        for key, repo_value in value.items():
            repo_type = ArtifactoryRepositoryType.from_string(key)
            if not repo_type:
                continue
            repo_str = str(repo_value).strip()
            if repo_str:
                normalized[repo_type] = repo_str
        return normalized

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

    def cli_install_url_value(self) -> str:
        """Return the configured jfrog CLI installer URL."""

        raw_url = (self.cli_install_url or '').strip()
        return raw_url or DEFAULT_JFROG_CLI_INSTALL_URL

    def repository_commands(self) -> Dict[ArtifactoryRepositoryType, str]:
        """Return jfrog CLI configuration commands per repository type."""

        commands: dict[ArtifactoryRepositoryType, str] = {}

        for repo_type, repo_key in self.repositories.items():
            normalized_repo = repo_key.strip()
            if not normalized_repo:
                continue

            repo_arg = shlex.quote(normalized_repo)
            server_arg = shlex.quote(self.server_id)

            template = COMMAND_TEMPLATES.get(repo_type)
            if not template:
                continue

            commands[repo_type] = template.format(
                server=server_arg, repo=repo_arg
            )

        return commands

