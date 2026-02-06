"""
Task Storage Module
إدارة حفظ وتحميل المهام
"""

from typing import Dict, Any, Optional, List
import logging
import json
from datetime import datetime
from pathlib import Path
import uuid

from ..config.settings import settings

logger = logging.getLogger(__name__)


class TaskStorage:
    """
    Task Storage Manager
    إدارة حفظ المهام (تخزين محلي)
    """
    
    def __init__(self):
        """Initialize task storage with configurable local directory"""
        from pathlib import Path
        import os
        
        # Get project root and use configurable path
        project_root = Path(os.getcwd())
        self.local_storage_dir = project_root / settings.local_tasks_dir
        self.local_storage_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"📁 Using local storage for tasks: {self.local_storage_dir}")
    
    def save_task(self, task_data: Dict[str, Any], task_id: str = None) -> Dict[str, Any]:
        """Save task to local storage"""
        try:
            # Generate ID if not provided
            if not task_id:
                task_id = task_data.get("id") or str(uuid.uuid4())
                task_data["id"] = task_id
            
            # Add timestamps
            now = datetime.now().isoformat()
            if "created_at" not in task_data:
                task_data["created_at"] = now
            task_data["updated_at"] = now
            
            file_path = self.local_storage_dir / f"{task_id}.json"
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(task_data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"✅ Saved task locally: {task_id}")
            return task_data
            
        except Exception as e:
            logger.error(f"❌ Failed to save task: {e}")
            raise

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Load task from local storage"""
        try:
            file_path = self.local_storage_dir / f"{task_id}.json"
            if not file_path.exists():
                return None
                
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"❌ Failed to load task {task_id}: {e}")
            return None

    def list_tasks(self, limit: int = 100, lawyer_id: str = None) -> List[Dict[str, Any]]:
        """List all tasks"""
        try:
            tasks = []
            for file_path in self.local_storage_dir.glob("*.json"):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if lawyer_id and data.get("lawyer_id") != lawyer_id:
                            continue
                        tasks.append(data)
                except:
                    continue
                    
            # Sort by created_at desc
            tasks.sort(key=lambda x: x.get("created_at", ""), reverse=True)
            return tasks[:limit]
        except Exception as e:
            logger.error(f"❌ Failed to list tasks: {e}")
            return []

    def delete_task(self, task_id: str) -> bool:
        """Delete a task"""
        try:
            file_path = self.local_storage_dir / f"{task_id}.json"
            if file_path.exists():
                file_path.unlink()
                logger.info(f"✅ Deleted task: {task_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to delete task {task_id}: {e}")
            return False
            
    def update_task_status(self, task_id: str, status: str) -> bool:
        """Update task status"""
        task = self.get_task(task_id)
        if not task:
            return False
        task["status"] = status
        self.save_task(task, task_id)
        return True


# Global instance
task_storage = TaskStorage()
