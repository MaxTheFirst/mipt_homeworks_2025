from fastapi import FastAPI, HTTPException, Query
from typing import Optional, Dict, Any
from pydantic import BaseModel
import os
import uvicorn

from homework_final.infrastructure.github_client import GitHubClient
from homework_final.service.csv_service import CSVService

app = FastAPI(
    title="GitHub Repository Search API",
    description="API для поиска репозиториев на GitHub и сохранения в CSV",
    version="1.0.0",
)

if not os.path.exists("static"):
    os.makedirs("static")


class SearchParams(BaseModel):
    limit: int = Query(10, ge=1, le=1000, description="Количество репозиториев")
    offset: int = Query(0, ge=0, description="Смещение (пагинация)")
    lang: str = Query(..., description="Язык программирования")
    stars_min: Optional[int] = Query(
        0, ge=0, description="Минимальное количество звезд"
    )
    stars_max: Optional[int] = Query(
        None, ge=0, description="Максимальное количество звезд"
    )
    forks_min: Optional[int] = Query(
        0, ge=0, description="Минимальное количество форков"
    )
    forks_max: Optional[int] = Query(
        None, ge=0, description="Максимальное количество форков"
    )


@app.get("/search/repositories", summary="Поиск репозиториев GitHub")
async def search_repositories(
    limit: int = Query(10, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    lang: str = Query(...),
    stars_min: Optional[int] = Query(0, ge=0),
    stars_max: Optional[int] = Query(None, ge=0),
    forks_min: Optional[int] = Query(0, ge=0),
    forks_max: Optional[int] = Query(None, ge=0),
) -> Dict[str, Any]:
    try:
        client = GitHubClient()
        csv_service = CSVService()

        query_parts = [f"language:{lang}"]

        if stars_min and stars_min > 0:
            query_parts.append(f"stars:>={stars_min}")
        if stars_max is not None:
            query_parts.append(f"stars:<={stars_max}")
        if forks_min and forks_min > 0:
            query_parts.append(f"forks:>={forks_min}")
        if forks_max is not None:
            query_parts.append(f"forks:<={forks_max}")

        query = " ".join(query_parts)

        repositories = await client.search_repositories(
            query=query, limit=limit, offset=offset
        )

        if not repositories:
            return {
                "message": "Репозитории не найдены",
                "filename": None,
                "count": 0,
                "filepath": None,
                "search_params": {"query": query, "limit": limit, "offset": offset},
            }

        filename = f"repositories_{lang}_{limit}_{offset}.csv"
        filepath = os.path.join("static", filename)

        await csv_service.save_to_csv(repositories, filepath)

        return {
            "message": "Репозитории успешно сохранены",
            "filename": filename,
            "count": len(repositories),
            "filepath": filepath,
            "search_params": {"query": query, "limit": limit, "offset": offset},
        }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Ошибка при поиске репозиториев: {str(e)}"
        )


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
