from fastapi import HTTPException
from typing import Dict, Any
import os

from homework_final.model.search_params import SearchParams
from homework_final.infrastructure.github_client import GitHubClient
from homework_final.service.csv_service import CSVService


class SearchService:
    async def search_repositories(
        self,
        search_param: SearchParams,
        client: GitHubClient,
        csv_service: CSVService,
    ) -> Dict[str, Any]:
        try:
            repositories = await client.search_repositories(search_param)

            if not repositories:
                return {
                    "message": "Репозитории не найдены",
                    "filename": None,
                    "count": 0,
                    "filepath": None,
                    "search_params": search_param,
                }

            filename = f"repositories_{search_param.lang}_{search_param.limit}_{search_param.offset}.csv"
            filepath = os.path.join("static", filename)

            await csv_service.save_to_csv(repositories, filepath)

            return {
                "message": "Репозитории успешно сохранены",
                "filename": filename,
                "count": len(repositories),
                "filepath": filepath,
                "search_params": search_param,
            }

        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Ошибка при поиске репозиториев: {str(e)}"
            )
