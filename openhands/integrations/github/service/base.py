import json
from typing import Any, cast

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


class GitHubMixinBase(BaseGitService, HTTPClient):
    """
    Declares common attributes and method signatures used across mixins.
    """

    BASE_URL: str
    GRAPHQL_URL: str

    async def _get_headers(self) -> dict:
        """Retrieve the GH Token from settings store to construct the headers."""
        if not self.token:
            latest_token = await self.get_latest_token()
            if latest_token:
                self.token = latest_token

        logger.debug(
            '[%s] Constructing GitHub headers token_available=%s base_url=%s',
            self.provider,
            bool(self.token),
            self.BASE_URL,
        )

        return {
            'Authorization': f'Bearer {self.token.get_secret_value() if self.token else ""}',
            'Accept': 'application/vnd.github.v3+json',
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
            async with httpx.AsyncClient() as client:
                github_headers = await self._get_headers()

                # Make initial request
                response = await self.execute_request(
                    client=client,
                    url=url,
                    headers=github_headers,
                    params=params,
                    method=method,
                )

                # Handle token refresh if needed
                if self.refresh and self._has_token_expired(response.status_code):
                    logger.debug(
                        '[%s] GitHub token expired during request to %s - refreshing',
                        self.provider,
                        url,
                    )
                    await self.get_latest_token()
                    github_headers = await self._get_headers()
                    response = await self.execute_request(
                        client=client,
                        url=url,
                        headers=github_headers,
                        params=params,
                        method=method,
                    )

                response.raise_for_status()
                headers: dict = {}
                if 'Link' in response.headers:
                    headers['Link'] = response.headers['Link']

                return response.json(), headers

        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def execute_graphql_query(
        self, query: str, variables: dict[str, Any]
    ) -> dict[str, Any]:
        try:
            async with httpx.AsyncClient() as client:
                github_headers = await self._get_headers()

                variables_preview = self._sanitize_for_logging(variables)
                query_preview = ' '.join(query.split())
                if len(query_preview) > 500:
                    query_preview = f'{query_preview[:500]}... [truncated]'
                logger.debug(
                    '[%s] Executing GitHub GraphQL query url=%s variables=%s query_preview=%s',
                    self.provider,
                    self.GRAPHQL_URL,
                    variables_preview,
                    query_preview,
                )

                response = await client.post(
                    self.GRAPHQL_URL,
                    headers=github_headers,
                    json={'query': query, 'variables': variables},
                )
                response.raise_for_status()

                result = response.json()
                if 'errors' in result:
                    raise UnknownException(
                        f'GraphQL query error: {json.dumps(result["errors"])}'
                    )

                logger.debug(
                    '[%s] GitHub GraphQL query succeeded status=%s keys=%s',
                    self.provider,
                    response.status_code,
                    list(result.keys()),
                )

                return dict(result)

        except httpx.HTTPStatusError as e:
            raise self.handle_http_status_error(e)
        except httpx.HTTPError as e:
            raise self.handle_http_error(e)

    async def verify_access(self) -> bool:
        url = f'{self.BASE_URL}'
        logger.debug('[%s] Verifying GitHub access via %s', self.provider, url)
        await self._make_request(url)
        logger.debug('[%s] GitHub access verification succeeded', self.provider)
        return True

    async def get_user(self):
        url = f'{self.BASE_URL}/user'
        logger.debug('[%s] Fetching GitHub user info from %s', self.provider, url)
        response, _ = await self._make_request(url)

        logger.debug(
            '[%s] GitHub user info retrieved keys=%s',
            self.provider,
            list(response.keys()),
        )

        return User(
            id=str(response.get('id', '')),
            login=cast(str, response.get('login') or ''),
            avatar_url=cast(str, response.get('avatar_url') or ''),
            company=response.get('company'),
            name=response.get('name'),
            email=response.get('email'),
        )
