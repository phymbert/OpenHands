from typing import Any

import httpx
from pydantic import SecretStr

from openhands.core.logger import openhands_logger as logger
from openhands.integrations.protocols.http_client import HTTPClient
from openhands.integrations.service_types import (
    BaseGitService,
    RequestMethod,
    UnknownException,
    User,
)
from openhands.utils.http_session import httpx_verify_option


class GitLabMixinBase(BaseGitService, HTTPClient):
    """
    Declares common attributes and method signatures used across mixins.
    """

    BASE_URL: str
    GRAPHQL_URL: str

    async def _get_headers(self) -> dict[str, Any]:
        """Retrieve the GitLab Token to construct the headers"""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        logger.debug(
            '[%s] Constructing GitLab headers token_available=%s base_url=%s',
            self.provider,
            bool(self.token),
            self.BASE_URL,
        )

        return {
            'Authorization': f'Bearer {self.token.get_secret_value()}',
        }

    async def get_latest_token(self) -> SecretStr | None:  # type: ignore[override]
        return self.token

    async def _make_request(
        self,
        url: str,
        params: dict | None = None,
        method: RequestMethod = RequestMethod.GET,
    ) -> tuple[Any, dict]:  # type: ignore[override]
        try:
            async with httpx.AsyncClient(verify=httpx_verify_option()) as client:
                gitlab_headers = await self._get_headers()

                # Make initial request
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=gitlab_headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    logger.debug(
                        '[%s] GitLab token expired during request to %s - refreshing',
                        self.provider,
                        url,
                    )
                    await self.get_latest_token()
                    gitlab_headers = await self._get_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=gitlab_headers,
                        params=params,
                        method=method,
                    )

                response.raise_for_status()
                headers = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                if 'X-Total' in response.headers:
                    headers['X-Total'] = response.headers['X-Total']

                content_type = response.headers.get('Content-Type', '')
                if 'application/json' in content_type:
                    return response.json(), headers
                else:
                    return response.text, headers

        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any] | None = None
    ) -> Any:
        """Execute a GraphQL query against the GitLab GraphQL API

        Args:
            query: The GraphQL query string
            variables: Optional variables for the GraphQL query

        Returns:
            The data portion of the GraphQL response
        """
        if variables is None:
            variables = {}
        try:
            async with httpx.AsyncClient(verify=httpx_verify_option()) as client:
                gitlab_headers = await self._get_headers()
                # Add content type header for GraphQL
                gitlab_headers['Content-Type'] = 'application/json'

                variables_preview = self._sanitize_for_logging(variables)
                query_preview = ' '.join(query.split())
                if len(query_preview) > 500:
                    query_preview = f'{query_preview[:500]}... [truncated]'
                logger.debug(
                    '[%s] Executing GitLab GraphQL query url=%s variables=%s query_preview=%s',
                    self.provider,
                    self.GRAPHQL_URL,
                    variables_preview,
                    query_preview,
                )

                payload = {
                    'query': query,
                    'variables': variables if variables is not None else {},
                }

                response = await client.post(
                    self.GRAPHQL_URL, headers=gitlab_headers, json=payload
                )

                if self.refresh and self._has_token_expired(response.status_code):
                    logger.debug(
                        '[%s] GitLab GraphQL token refresh triggered for %s',
                        self.provider,
                        self.GRAPHQL_URL,
                    )
                    await self.get_latest_token()
                    gitlab_headers = await self._get_headers()
                    gitlab_headers['Content-Type'] = 'application/json'
                    response = await client.post(
                        self.GRAPHQL_URL, headers=gitlab_headers, json=payload
                    )

                response.raise_for_status()
                result = response.json()

                # Check for GraphQL errors
                if 'errors' in result:
                    error_message = result['errors'][0].get(
                        'message', 'Unknown GraphQL error'
                    )
                    logger.debug(
                        '[%s] GitLab GraphQL query returned errors=%s',
                        self.provider,
                        result['errors'],
                    )
                    raise UnknownException(f'GraphQL error: {error_message}')

                logger.debug(
                    '[%s] GitLab GraphQL query succeeded status=%s keys=%s',
                    self.provider,
                    response.status_code,
                    list(result.keys()),
                )

                return result.get('data')
        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def get_user(self) -> User:
        url = f'{self.BASE_URL}/user'
        logger.debug('[%s] Fetching GitLab user info from %s', self.provider, url)
        response, _ = await self._make_request(url)

        # Use a default avatar URL if not provided
        # In some self-hosted GitLab instances, the avatar_url field may be returned as None.
        avatar_url = response.get('avatar_url') or ''

        logger.debug(
            '[%s] GitLab user info retrieved keys=%s',
            self.provider,
            list(response.keys()),
        )

        return User(
            id=str(response.get('id', '')),
            login=response.get('username'),  # type: ignore[call-arg]
            avatar_url=avatar_url,
            name=response.get('name'),
            email=response.get('email'),
            company=response.get('organization'),
        )

    def _extract_project_id(self, repository: str) -> str:
        """Extract project_id from repository name for GitLab API calls.

        Args:
            repository: Repository name in format 'owner/repo' or 'domain/owner/repo'

        Returns:
            URL-encoded project ID for GitLab API
        """
        if '/' in repository:
            parts = repository.split('/')
            if len(parts) >= 3 and '.' in parts[0]:
                # Self-hosted GitLab: 'domain/owner/repo' -> 'owner/repo'
                project_id = '/'.join(parts[1:]).replace('/', '%2F')
            else:
                # Regular GitLab: 'owner/repo' -> 'owner/repo'
                project_id = repository.replace('/', '%2F')
        else:
            project_id = repository

        logger.debug(
            '[%s] Extracted GitLab project id repository=%s resolved=%s',
            self.provider,
            repository,
            project_id,
        )

        return project_id
