from pydantic import BaseModel, ConfigDict, Field, ValidationError


class KubernetesConfig(BaseModel):
    """Configuration for Kubernetes runtime.

    Attributes:
        namespace: The Kubernetes namespace to use for OpenHands resources
        ingress_domain: Domain for ingress resources
        pvc_storage_size: Size of the persistent volume claim (e.g. "2Gi")
        pvc_storage_class: Storage class for persistent volume claims
        resource_cpu_request: CPU request for runtime pods
        resource_memory_request: Memory request for runtime pods
        resource_memory_limit: Memory limit for runtime pods
        image_pull_secret: Optional name of image pull secret for private registries
        ingress_tls_secret: Optional name of TLS secret for ingress
        node_selector_key: Optional node selector key for pod scheduling
        node_selector_val: Optional node selector value for pod scheduling
        tolerations_yaml: Optional YAML string defining pod tolerations
    """

    namespace: str = Field(
        default='default',
        description='The Kubernetes namespace to use for OpenHands resources',
    )
    ingress_domain: str = Field(
        default='localhost', description='Domain for ingress resources'
    )
    pvc_storage_size: str = Field(
        default='2Gi', description='Size of the persistent volume claim'
    )
    pvc_storage_class: str | None = Field(
        default=None, description='Storage class for persistent volume claims'
    )
    resource_cpu_request: str = Field(
        default='1', description='CPU request for runtime pods'
    )
    resource_memory_request: str = Field(
        default='1Gi', description='Memory request for runtime pods'
    )
    resource_memory_limit: str = Field(
        default='2Gi', description='Memory limit for runtime pods'
    )
    image_pull_secret: str | None = Field(
        default=None,
        description='Optional name of image pull secret for private registries',
    )
    ingress_tls_secret: str | None = Field(
        default=None, description='Optional name of TLS secret for ingress'
    )
    node_selector_key: str | None = Field(
        default=None, description='Optional node selector key for pod scheduling'
    )
    node_selector_val: str | None = Field(
        default=None, description='Optional node selector value for pod scheduling'
    )
    tolerations_yaml: str | None = Field(
        default=None, description='Optional YAML string defining pod tolerations'
    )
    privileged: bool = Field(
        default=False,
        description='Run the runtime sandbox container in privileged mode for use with docker-in-docker',
    )
    allow_privilege_escalation: bool | None = Field(
        default=None,
        description='Allow processes in the runtime sandbox container to escalate privileges',
    )
    read_only_root_filesystem: bool | None = Field(
        default=None,
        description='Mount the runtime sandbox container root filesystem as read-only',
    )
    run_as_non_root: bool | None = Field(
        default=None,
        description='Require the runtime sandbox container to run as a non-root user',
    )
    run_as_user: int | None = Field(
        default=None,
        description='Override the user ID used for the runtime sandbox container',
    )
    run_as_group: int | None = Field(
        default=None,
        description='Override the primary group ID used for the runtime sandbox container',
    )
    mount_tmp_empty_dir: bool = Field(
        default=False,
        description='Mount /tmp inside the runtime sandbox as an ephemeral emptyDir volume',
    )
    enable_memory_dshm_volume: bool = Field(
        default=False,
        description=(
            'Mount /dev/shm as an in-memory emptyDir volume to increase shared memory capacity'
        ),
    )
    memory_dshm_volume_size_limit: str | None = Field(
        default=None,
        description=(
            'Optional size limit for the /dev/shm emptyDir volume (e.g. "1Gi"). Only applied when '
            'enable_memory_dshm_volume is true.'
        ),
    )

    model_config = ConfigDict(extra='forbid')

    @classmethod
    def from_toml_section(cls, data: dict) -> dict[str, 'KubernetesConfig']:
        """Create a mapping of KubernetesConfig instances from a toml dictionary representing the [kubernetes] section.

        The configuration is built from all keys in data.

        Returns:
            dict[str, KubernetesConfig]: A mapping where the key "kubernetes" corresponds to the [kubernetes] configuration
        """
        # Initialize the result mapping
        kubernetes_mapping: dict[str, KubernetesConfig] = {}

        # Try to create the configuration instance
        try:
            kubernetes_mapping['kubernetes'] = cls.model_validate(data)
        except ValidationError as e:
            raise ValueError(f'Invalid kubernetes configuration: {e}')

        return kubernetes_mapping
