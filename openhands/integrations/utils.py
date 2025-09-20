from typing import Literal

from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.bitbucket.bitbucket_service import BitBucketService
from openhands.integrations.github.github_service import GitHubService
from openhands.integrations.gitlab.gitlab_service import GitLabService
from openhands.integrations.provider import ProviderType


async def validate_provider_token(
    token: SecretStr,
    base_domain: str | None = None,
    bitbucket_mode: Literal['cloud', 'server'] | None = None,
) -> ProviderType | None:
    """Determine whether a token is for GitHub, GitLab, or Bitbucket by attempting to get user info
    from the services.

    Args:
        token: The token to check
        base_domain: Optional base domain for the service

    Returns:
        'github' if it's a GitHub token
        'gitlab' if it's a GitLab token
        'bitbucket' if it's a Bitbucket token
        None if the token is invalid for all services
    """
    # Skip validation for empty tokens
    if token is None:
        return None  # type: ignore[unreachable]

    logger.debug(
        'Validating provider token base_domain=%s bitbucket_mode=%s',
        base_domain,
        bitbucket_mode,
    )

    # Try GitHub first
    github_error = None
    try:
        logger.debug('Attempting GitHub token validation')
        github_service = GitHubService(token=token, base_domain=base_domain)
        await github_service.verify_access()
        logger.debug('Token validated for GitHub provider')
        return ProviderType.GITHUB
    except Exception as e:
        github_error = e
        logger.debug('GitHub token validation failed: %s', e, exc_info=True)

    # Try GitLab next
    gitlab_error = None
    try:
        logger.debug('Attempting GitLab token validation')
        gitlab_service = GitLabService(token=token, base_domain=base_domain)
        await gitlab_service.get_user()
        logger.debug('Token validated for GitLab provider')
        return ProviderType.GITLAB
    except Exception as e:
        gitlab_error = e
        logger.debug('GitLab token validation failed: %s', e, exc_info=True)

    # Try Bitbucket last
    bitbucket_error = None
    try:
        if bitbucket_mode is not None:
            resolved_mode = bitbucket_mode
        elif base_domain and base_domain != 'bitbucket.org':
            resolved_mode = 'server'
        else:
            resolved_mode = 'cloud'

        bitbucket_service = BitBucketService(
            token=token,
            base_domain=base_domain,
            bitbucket_mode=resolved_mode,
        )
        await bitbucket_service.get_user()
        logger.debug('Token validated for Bitbucket provider mode=%s', resolved_mode)
        return ProviderType.BITBUCKET
    except Exception as e:
        bitbucket_error = e
        logger.debug('Bitbucket token validation failed: %s', e, exc_info=True)

    logger.debug(
        f'Failed to validate token: {github_error} \n {gitlab_error} \n {bitbucket_error}'
    )

    return None
