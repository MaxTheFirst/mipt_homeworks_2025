import httpx
from typing import List, Dict, Any, Mapping, Union
import asyncio
import time


class GitHubClient:
    BASE_URL: str = "https://api.github.com"

    def __init__(self, timeout: int = 30) -> None:
        self.timeout = timeout
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "GitHub-Search-API/1.0",
        }

    async def search_repositories(
        self, query: str, limit: int = 10, offset: int = 0
    ) -> List[Dict[str, Any]]:
        all_repositories: List[Dict[str, Any]] = []

        per_page = min(100, limit)
        page = max(1, (offset // per_page) + 1)
        intra_page_offset = offset % per_page

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            try:
                while len(all_repositories) < limit:
                    params: Mapping[str, Union[str, int]] = {
                        "q": query,
                        "sort": "stars",
                        "order": "desc",
                        "per_page": str(per_page),
                        "page": str(page),
                    }

                    response = await client.get(
                        f"{self.BASE_URL}/search/repositories",
                        params=params,
                        headers=self.headers,
                    )

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
                        if len(all_repositories) >= limit:
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

                    await asyncio.sleep(0.5)

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

        return all_repositories
