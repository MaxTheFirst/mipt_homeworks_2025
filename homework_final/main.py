from fastapi import FastAPI, Depends
from typing import Dict, Any
import os
import uvicorn

from homework_final.model.search_params import SearchParams
from homework_final.service.search_service import SearchService
from homework_final.infrastructure.github_client import GitHubClient
from homework_final.service.csv_service import CSVService
from homework_final.dependencies import (
    get_search_service,
    get_github_client,
    get_csv_service,
)

app = FastAPI(
    title="GitHub Repository Search API",
    description="API для поиска репозиториев на GitHub и сохранения в CSV",
    version="1.0.0",
)


@app.get("/search/repositories", summary="Поиск репозиториев GitHub")
async def search_repositories(
    search_param: SearchParams,
    search_service: SearchService = Depends(get_search_service),
    client: GitHubClient = Depends(get_github_client),
    csv_service: CSVService = Depends(get_csv_service),
) -> Dict[str, Any]:
    return await search_service.search_repositories(search_param, client, csv_service)


def main():
    if not os.path.exists("static"):
        os.makedirs("static")

    uvicorn.run(app, host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
