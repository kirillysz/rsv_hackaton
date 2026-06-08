from app.utils.yougile.service import YougileClient


class YouGileExecutor:
    def __init__(self, client: YougileClient):
        self.client = client

    async def execute(self, data: dict):
        actions = data.get("actions", [])

        if not isinstance(actions, list):
            return [{"error": "actions must be a list"}]

        results = []

        for action in actions:
            if not isinstance(action, dict):
                continue

            action_type = action.get("type")

            if action_type == "create_task":
                results.append(await self._create_task(action))

            elif action_type == "set_task_complete":
                results.append(await self._complete_task(action))

            else:
                results.append({"error": f"Unknown action type: {action_type}"})

        return results

    async def _create_task(self, action: dict):
        return await self.client.create_task(
            title=action.get("title"),
            deadline=action.get("deadline"),
            assigned=action.get("assigned", [])
        )

    async def _complete_task(self, action: dict):
        return await self.client.set_task_complete(
            task_id=action.get("task_id")
        )