from homework_final.config import BASE_GITHUB_URL
from homework_final.infrastructure.github_client import GitHubClient


def get_github_client() -> GitHubClient:
    return GitHubClient(BASE_GITHUB_URL)


def get_search_service():
    from homework_final.service.search_service import SearchService

    return SearchService()


def get_csv_service():
    from homework_final.service.csv_service import CSVService

    return CSVService()
