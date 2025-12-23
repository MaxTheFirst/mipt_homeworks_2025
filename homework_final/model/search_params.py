from fastapi import Query
from typing import Optional
from pydantic import BaseModel


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
