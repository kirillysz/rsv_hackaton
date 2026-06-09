import httpx

from config import settings

class YougileClient:
    def __init__(self, token: str):
        self.base_url = "https://ru.yougile.com/api-v2"
        self.token = token

    async def _request(self, method: str, path: str, json=None):
        async with httpx.AsyncClient() as client:
            resp = await client.request(
                method,
                self.base_url + path,
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json=json
            )

            resp.raise_for_status()
            return resp.json()
        
    async def create_task(self, title: str, deadline: int | None = None, assigned=None):
        if deadline is not None:
            return await self._request(
                "POST",
                "/tasks",
                json={
                    "title": title,
                    "columnId": settings.COLUMN_ID,
                    "assigned": assigned or [],
                    "deadline": {
                        "deadline": deadline
                    }
                }
            )
        else:
            return await self._request(
                "POST",
                "/tasks",
                json={
                    "title": title,
                    "columnId": settings.COLUMN_ID,
                    "assigned": assigned or []
                }
            )
    
    async def set_task_complete(self, task_id: str):
        return await self._request(
            "PUT",
            f"/tasks/{task_id}",
            json={
                "completed": True
            }
        )
    
    async def get_tasks(self, column_id: str) -> list[dict]:
        data = await self._request(
            "GET",
            f"/task-list",
            json={
                "column_id": column_id
            }
        )
        return data.get("content", [])
