import asyncio
from typing import Dict, Any, Callable
import uuid

class BackgroundTaskRunner:
    def __init__(self):
        self.tasks: Dict[str, Dict[str, Any]] = {}

    async def run_task(self, func: Callable, *args, **kwargs) -> str:
        """Run a function in background and return task ID"""
        task_id = str(uuid.uuid4())
        # Create coroutine task
        task = asyncio.create_task(self._run_and_store(task_id, func, *args, **kwargs))
        self.tasks[task_id] = {
            'task': task,
            'status': 'running',
            'result': None,
            'created_at': asyncio.get_event_loop().time()
        }
        return task_id

    async def _run_and_store(self, task_id: str, func: Callable, *args, **kwargs):
        """Execute function and store result"""
        try:
            if asyncio.iscoroutinefunction(func):
                result = await func(*args, **kwargs)
            else:
                # Run sync function in thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, func, *args, **kwargs)

            self.tasks[task_id]['result'] = result
            self.tasks[task_id]['status'] = 'completed'
        except Exception as e:
            self.tasks[task_id]['result'] = str(e)
            self.tasks[task_id]['status'] = 'failed'

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """Get task status and result if completed"""
        if task_id not in self.tasks:
            return {'status': 'not_found'}

        task_info = self.tasks[task_id]
        return {
            'status': task_info['status'],
            'result': task_info['result'] if task_info['status'] in ['completed', 'failed'] else None
        }

    def cleanup_old_tasks(self, max_age_seconds=3600):
        """Remove tasks older than max_age"""
        current_time = asyncio.get_event_loop().time()
        to_delete = []
        for task_id, task_info in self.tasks.items():
            if current_time - task_info['created_at'] > max_age_seconds:
                to_delete.append(task_id)
        for task_id in to_delete:
            del self.tasks[task_id]
