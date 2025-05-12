# File: lms/canvas/mixins/request_mixin.py
"""
Mixin providing core request functionality for Canvas API client.
"""
import logging
import httpx
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class RequestMixin:
    """Provides core API request functionality"""

    async def request(
            self,
            method: str,
            endpoint: str,
            params: Optional[Dict] = None,
            data: Optional[Dict] = None,
    ) -> Any:
        """Make an async request to the Canvas API using httpx"""
        url = f"{self.base_url}/api/v1/{endpoint}"
        params = params or {}
        data = data or {}

        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=self.headers,
                    params=params,
                    json=data if method.lower() in ["post", "put"] else None,
                )
                response.raise_for_status()

                result = response.json()
                if isinstance(result, list) and "link" in response.headers:
                    while "next" in response.headers.get("link", ""):
                        links = response.headers.get("link").split(",")
                        next_url = None
                        for link in links:
                            if 'rel="next"' in link:
                                next_url = link.split(";")[0].strip("<> ")
                                break
                        if not next_url:
                            break
                        next_response = await client.get(next_url, headers=self.headers)
                        next_response.raise_for_status()
                        next_result = next_response.json()
                        result.extend(next_result)
                        if (
                                "link" not in next_response.headers
                                or "next" not in next_response.headers.get("link", "")
                        ):
                            break
                return result
            except httpx.HTTPError as e:
                logger.error(f"API request error: {e}")
                raise