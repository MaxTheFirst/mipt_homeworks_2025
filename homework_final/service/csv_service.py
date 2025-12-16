import aiofiles
import csv
from typing import List, Dict, Any
import os
import io


class CSVService:
    CSV_HEADERS: List[str] = [
        "name",
        "full_name",
        "html_url",
        "description",
        "language",
        "stars",
        "forks",
        "created_at",
        "updated_at",
        "license",
        "topics",
        "owner_login",
        "owner_type",
    ]

    async def save_to_csv(
        self, repositories: List[Dict[str, Any]], filepath: str
    ) -> None:
        if not repositories:
            return

        os.makedirs(os.path.dirname(filepath), exist_ok=True)

        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.CSV_HEADERS,
            delimiter=",",
            quotechar='"',
            quoting=csv.QUOTE_MINIMAL,
        )

        writer.writeheader()

        for repo in repositories:
            row: Dict[str, Any] = {}
            for header in self.CSV_HEADERS:
                value = repo.get(header, "")
                if value is None:
                    value = ""
                elif isinstance(value, str):
                    value = (
                        value.replace('"', '""').replace("\n", " ").replace("\r", "")
                    )
                row[header] = value
            writer.writerow(row)

        csv_content = output.getvalue()
        async with aiofiles.open(filepath, mode="w", encoding="utf-8") as f:
            await f.write(csv_content)

    async def read_from_csv(self, filepath: str) -> List[Dict[str, Any]]:
        if not os.path.exists(filepath):
            return []

        repositories: List[Dict[str, Any]] = []

        async with aiofiles.open(filepath, mode="r", encoding="utf-8") as f:
            content = await f.read()

        csv_file = io.StringIO(content)
        reader = csv.DictReader(csv_file)

        for row in reader:
            try:
                row["stars"] = int(row.get("stars", "0") or "0")
            except (ValueError, KeyError):
                row["stars"] = 0

            try:
                row["forks"] = int(row.get("forks", "0") or "0")
            except (ValueError, KeyError):
                row["forks"] = 0

            repositories.append(row)

        return repositories
