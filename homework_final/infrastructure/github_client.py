import httpx
from typing import List, Dict, Any, Mapping, Union, Optional
import time

from homework_final.model.search_params import SearchParams


class GitHubClient:
    def __init__(
        self, base_url: str, timeout: int = 30, error_timeout: float = 0.5
    ) -> None:
        self.base_url = base_url
        self.timeout = timeout
        self.error_timeout = error_timeout
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Search-API/1.0",
        }
        self._session: Optional[httpx.AsyncClient] = None

    async def get_new_session(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(timeout=self.timeout)

    async def get_session(self) -> httpx.AsyncClient:
        if self._session is None or self._session.is_closed:
            self._session = await self.get_new_session()

        if not self._session.is_closed:
            await self._session.aclose()
            self._session = await self.get_new_session()

        return self._session

    @staticmethod
    def get_query(params_data: SearchParams) -> str:
        query_parts = [f"language:{params_data.lang}"]

        if params_data.stars_min and params_data.stars_min > 0:
            query_parts.append(f"stars:>={params_data.stars_min}")
        if params_data.stars_max is not None:
            query_parts.append(f"stars:<={params_data.stars_max}")
        if params_data.forks_min and params_data.forks_min > 0:
            query_parts.append(f"forks:>={params_data.forks_min}")
        if params_data.forks_max is not None:
            query_parts.append(f"forks:<={params_data.forks_max}")

        return " ".join(query_parts)

    async def search_repositories(
        self, params_data: SearchParams
    ) -> List[Dict[str, Any]]:
        all_repositories: List[Dict[str, Any]] = []

        per_page = min(100, params_data.limit)
        page = max(1, (params_data.offset // per_page) + 1)
        intra_page_offset = params_data.offset % per_page

        query = self.get_query(params_data)

        session = await self.get_session()

        while len(all_repositories) < params_data.limit:
            params: Mapping[str, Union[str, int]] = {
                "q": query,
                "sort": "stars",
                "order": "desc",
                "per_page": str(per_page),
                "page": str(page),
            }

            try:
                response = await session.get(
                    f"{self.base_url}/search/repositories",
                    params=params,
                    headers=self.headers,
                )
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 422:
                    raise Exception(
                        f"Некорректный запрос к GitHub API: {e.response.text}"
                    )
                elif e.response.status_code == 403:
                    try:
                        reset_time = int(
                            e.response.headers.get("X-RateLimit-Reset", "0")
                        )
                        if reset_time:
                            wait_time = reset_time - int(time.time())
                            if wait_time > 0:
                                raise Exception(
                                    f"Лимит запросов исчерпан. Подождите {wait_time} секунд."
                                )
                    except (ValueError, KeyError):
                        pass
                    raise Exception("Превышен лимит запросов к GitHub API")
                else:
                    raise Exception(
                        f"Ошибка GitHub API: {e.response.status_code} - {e.response.text}"
                    )
            except httpx.RequestError as e:
                raise Exception(f"Ошибка соединения: {str(e)}")

            if response.status_code == 403:
                if "rate limit" in response.text.lower():
                    raise Exception(
                        "Превышен лимит запросов к GitHub API. Попробуйте позже."
                    )

            response.raise_for_status()
            data = response.json()

            items = data.get("items", [])
            if not items:
                break

            start_idx = intra_page_offset if page == 1 else 0
            items_to_process = items[start_idx:]

            for repo in items_to_process:
                if len(all_repositories) >= params_data.limit:
                    break

                repository_data: Dict[str, Any] = {
                    "name": repo.get("name", ""),
                    "full_name": repo.get("full_name", ""),
                    "html_url": repo.get("html_url", ""),
                    "description": repo.get("description", "") or "",
                    "language": repo.get("language", "") or "",
                    "stars": repo.get("stargazers_count", 0),
                    "forks": repo.get("forks_count", 0),
                    "created_at": repo.get("created_at", ""),
                    "updated_at": repo.get("updated_at", ""),
                    "license": repo.get("license", {}).get("name", "")
                    if repo.get("license")
                    else "",
                    "topics": ", ".join(repo.get("topics", [])),
                    "owner_login": repo.get("owner", {}).get("login", ""),
                    "owner_type": repo.get("owner", {}).get("type", ""),
                }
                all_repositories.append(repository_data)

            if len(items) < per_page:
                break

            page += 1
            intra_page_offset = 0

        return all_repositories
