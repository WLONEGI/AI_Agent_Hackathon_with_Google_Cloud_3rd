from typing import Dict, Any, Optional
import uuid
from datetime import datetime

class WorkflowManager:
    def __init__(self):
        # In-memory storage for workflow states
        # Key: workflow_id, Value: dict containing state and data
        self.workflows: Dict[str, Dict[str, Any]] = {}

    def create_workflow(self, initial_input: str) -> str:
        workflow_id = str(uuid.uuid4())
        self.workflows[workflow_id] = {
            "id": workflow_id,
            "status": "created",
            "created_at": datetime.now().isoformat(),
            "input": initial_input,
            "current_phase": 0,
            "data": {
                "story": None,
                "characters": [],
                "storyboard": None,
                "panels": [],
                "pages": []
            },
            "history": []
        }
        return workflow_id

    def get_workflow(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        return self.workflows.get(workflow_id)

    def update_phase(self, workflow_id: str, phase: int, status: str, result: Any = None):
        if workflow_id in self.workflows:
            self.workflows[workflow_id]["current_phase"] = phase
            self.workflows[workflow_id]["status"] = status
            if result:
                # Update specific data based on phase
                if phase == 1:
                    self.workflows[workflow_id]["data"]["story"] = result
                elif phase == 2:
                    self.workflows[workflow_id]["data"]["characters"] = result
                # Add more phase mappings as needed
            
            self.workflows[workflow_id]["history"].append({
                "phase": phase,
                "status": status,
                "timestamp": datetime.now().isoformat()
            })

workflow_manager = WorkflowManager()
