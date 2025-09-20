from __future__ import annotations

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    SecretStr,
    SerializationInfo,
    field_serializer,
    field_validator,
    model_validator,
)
from pydantic.json import pydantic_encoder

from openhands.core.config.artifactory_config import (
    ArtifactoryConfig,
    ArtifactoryRepositoryType,
)
from openhands.core.config.llm_config import LLMConfig
from openhands.core.config.mcp_config import MCPConfig
from openhands.core.config.utils import load_openhands_config
from openhands.storage.data_models.user_secrets import UserSecrets


class Settings(BaseModel):
    """Persisted settings for OpenHands sessions"""

    language: str | None = None
    agent: str | None = None
    max_iterations: int | None = None
    security_analyzer: str | None = None
    confirmation_mode: bool | None = None
    llm_model: str | None = None
    llm_api_key: SecretStr | None = None
    llm_base_url: str | None = None
    remote_runtime_resource_factor: int | None = None
    # Planned to be removed from settings
    secrets_store: UserSecrets = Field(default_factory=UserSecrets, frozen=True)
    enable_default_condenser: bool = True
    enable_sound_notifications: bool = False
    enable_proactive_conversation_starters: bool = True
    enable_solvability_analysis: bool = True
    user_consents_to_analytics: bool | None = None
    sandbox_base_container_image: str | None = None
    sandbox_runtime_container_image: str | None = None
    mcp_config: MCPConfig | None = None
    search_api_key: SecretStr | None = None
    sandbox_api_key: SecretStr | None = None
    max_budget_per_task: float | None = None
    # Maximum number of events in the conversation view before condensation runs
    condenser_max_size: int | None = None
    email: str | None = None
    email_verified: bool | None = None
    git_user_name: str | None = None
    git_user_email: str | None = None
    artifactory_host: str | None = None
    artifactory_cli_install_url: str | None = None
    artifactory_api_key: SecretStr | None = None
    artifactory_repositories: dict[ArtifactoryRepositoryType, str] = Field(
        default_factory=dict
    )

    model_config = ConfigDict(validate_assignment=True, use_enum_values=True)

    @field_serializer('llm_api_key', 'search_api_key', 'artifactory_api_key')
    def api_key_serializer(self, api_key: SecretStr | None, info: SerializationInfo):
        """Custom serializer for API keys.

        To serialize the API key instead of ********, set expose_secrets to True in the serialization context.
        """
        if api_key is None:
            return None

        # Get the secret value to check if it's empty
        secret_value = api_key.get_secret_value()
        if not secret_value or not secret_value.strip():
            return None

        context = info.context
        if context and context.get('expose_secrets', False):
            return secret_value

        return pydantic_encoder(api_key)

    @model_validator(mode='before')
    @classmethod
    def convert_provider_tokens(cls, data: dict | object) -> dict | object:
        """Convert provider tokens from JSON format to UserSecrets format."""
        if not isinstance(data, dict):
            return data

        secrets_store = data.get('secrets_store')
        if not isinstance(secrets_store, dict):
            return data

        custom_secrets = secrets_store.get('custom_secrets')
        tokens = secrets_store.get('provider_tokens')

        secret_store = UserSecrets(provider_tokens={}, custom_secrets={})  # type: ignore[arg-type]

        if isinstance(tokens, dict):
            converted_store = UserSecrets(provider_tokens=tokens)  # type: ignore[arg-type]
            secret_store = secret_store.model_copy(
                update={'provider_tokens': converted_store.provider_tokens}
            )
        else:
            secret_store.model_copy(update={'provider_tokens': tokens})

        if isinstance(custom_secrets, dict):
            converted_store = UserSecrets(custom_secrets=custom_secrets)  # type: ignore[arg-type]
            secret_store = secret_store.model_copy(
                update={'custom_secrets': converted_store.custom_secrets}
            )
        else:
            secret_store = secret_store.model_copy(
                update={'custom_secrets': custom_secrets}
            )
        data['secret_store'] = secret_store
        return data

    @field_validator('condenser_max_size')
    @classmethod
    def validate_condenser_max_size(cls, v: int | None) -> int | None:
        if v is None:
            return v
        if v < 20:
            raise ValueError('condenser_max_size must be at least 20')
        return v

    @field_serializer('secrets_store')
    def secrets_store_serializer(self, secrets: UserSecrets, info: SerializationInfo):
        """Custom serializer for secrets store."""
        """Force invalidate secret store"""
        return {'provider_tokens': {}}

    @field_validator('artifactory_cli_install_url', mode='before')
    @classmethod
    def normalize_artifactory_cli_install_url(
        cls, value: str | None
    ) -> str | None:
        if value is None:
            return None
        trimmed = str(value).strip()
        return trimmed or None

    @field_validator('artifactory_repositories', mode='before')
    @classmethod
    def normalize_artifactory_repositories(
        cls, repositories: dict | None
    ) -> dict[ArtifactoryRepositoryType, str]:
        if repositories is None:
            return {}
        if not isinstance(repositories, dict):
            raise ValueError('artifactory_repositories must be a mapping')

        normalized: dict[ArtifactoryRepositoryType, str] = {}
        for key, value in repositories.items():
            if value is None:
                continue
            repo_value = str(value).strip()
            if not repo_value:
                continue
            repo_type = (
                key
                if isinstance(key, ArtifactoryRepositoryType)
                else ArtifactoryRepositoryType.from_string(str(key))
            )
            if repo_type is None:
                continue
            normalized[repo_type] = repo_value
        return normalized

    @field_serializer('artifactory_repositories')
    def serialize_artifactory_repositories(
        self,
        repositories: dict[ArtifactoryRepositoryType, str],
        info: SerializationInfo,
    ) -> dict[str, str]:
        serialized: dict[str, str] = {}
        for repo_type, repo_key in repositories.items():
            if not repo_key:
                continue
            key = (
                repo_type.value
                if isinstance(repo_type, ArtifactoryRepositoryType)
                else str(repo_type)
            )
            serialized[key] = repo_key
        return serialized

    @staticmethod
    def from_config() -> Settings | None:
        app_config = load_openhands_config()
        llm_config: LLMConfig = app_config.get_llm_config()
        if llm_config.api_key is None:
            # If no api key has been set, we take this to mean that there is no reasonable default
            return None
        security = app_config.security

        # Get MCP config if available
        mcp_config = None
        if hasattr(app_config, 'mcp'):
            mcp_config = app_config.mcp

        artifactory_config: ArtifactoryConfig = app_config.artifactory
        settings = Settings(
            language='en',
            agent=app_config.default_agent,
            max_iterations=app_config.max_iterations,
            security_analyzer=security.security_analyzer,
            confirmation_mode=security.confirmation_mode,
            llm_model=llm_config.model,
            llm_api_key=llm_config.api_key,
            llm_base_url=llm_config.base_url,
            remote_runtime_resource_factor=app_config.sandbox.remote_runtime_resource_factor,
            mcp_config=mcp_config,
            search_api_key=app_config.search_api_key,
            max_budget_per_task=app_config.max_budget_per_task,
            artifactory_host=artifactory_config.host,
            artifactory_cli_install_url=artifactory_config.cli_install_url_value(),
            artifactory_api_key=artifactory_config.api_key,
            artifactory_repositories=artifactory_config.repositories,
        )
        return settings

    def merge_with_config_settings(self) -> 'Settings':
        """Merge config.toml settings with stored settings.

        Config.toml takes priority for MCP settings, but they are merged rather than replaced.
        This method can be used by both server mode and CLI mode.
        """
        # Get config.toml settings
        config_settings = Settings.from_config()
        if not config_settings:
            return self

        if config_settings.artifactory_host and not self.artifactory_host:
            self.artifactory_host = config_settings.artifactory_host

        if (
            config_settings.artifactory_cli_install_url
            and not self.artifactory_cli_install_url
        ):
            self.artifactory_cli_install_url = (
                config_settings.artifactory_cli_install_url
            )

        if config_settings.artifactory_api_key:
            if not self.artifactory_api_key or not self.artifactory_api_key.get_secret_value().strip():
                self.artifactory_api_key = config_settings.artifactory_api_key

        if config_settings.artifactory_repositories:
            merged_repositories: dict[ArtifactoryRepositoryType, str] = dict(
                config_settings.artifactory_repositories
            )
            merged_repositories.update(self.artifactory_repositories)
            self.artifactory_repositories = merged_repositories

        if not config_settings.mcp_config:
            return self

        # If stored settings don't have MCP config, use config.toml MCP config
        if not self.mcp_config:
            self.mcp_config = config_settings.mcp_config
            return self

        # Both have MCP config - merge them with config.toml taking priority
        merged_mcp = MCPConfig(
            sse_servers=list(config_settings.mcp_config.sse_servers)
            + list(self.mcp_config.sse_servers),
            stdio_servers=list(config_settings.mcp_config.stdio_servers)
            + list(self.mcp_config.stdio_servers),
            shttp_servers=list(config_settings.mcp_config.shttp_servers)
            + list(self.mcp_config.shttp_servers),
        )

        # Create new settings with merged MCP config
        self.mcp_config = merged_mcp
        return self
