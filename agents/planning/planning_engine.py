"""
Planning Engine
محرك التخطيط - يبني خطة تنفيذ من المهام
"""

import logging
import uuid
from typing import List, Dict, Set
from agents.planning.task_models import Task, ExecutionStep, ExecutionPlan, TaskStatus

logger = logging.getLogger(__name__)


class PlanningEngine:
    """Creates execution plans from tasks"""
    
    def create_plan(self, tasks: List[Task]) -> ExecutionPlan:
        """
        Create execution plan from tasks
        
        Args:
            tasks: List of tasks to execute
            
        Returns:
            ExecutionPlan with ordered steps
        """
        logger.info(f"📋 Creating execution plan for {len(tasks)} tasks")
        
        # Create plan
        plan = ExecutionPlan(id=str(uuid.uuid4()))
        
        # Build dependency graph
        graph = self._build_dependency_graph(tasks)
        
        # Topological sort to get execution order
        try:
            ordered_tasks = self._topological_sort(graph, tasks)
        except ValueError as e:
            logger.error(f"❌ Cyclic dependency detected: {e}")
            # Fallback: execute in original order
            ordered_tasks = tasks
        
        # Convert to execution steps
        for task in ordered_tasks:
            step = ExecutionStep(
                id=task.id,
                task=task,
                status=TaskStatus.PENDING,
                estimated_time=self._estimate_time(task)
            )
            plan.add_step(step)
        
        logger.info(f"✅ Plan created with {len(plan.steps)} steps")
        logger.info(f"⏱️ Estimated time: {plan.total_estimated_time}s")
        
        return plan
    
    def _build_dependency_graph(self, tasks: List[Task]) -> Dict[str, Set[str]]:
        """Build dependency graph from tasks"""
        
        graph = {task.id: set(task.depends_on) for task in tasks}
        return graph
    
    def _topological_sort(self, graph: Dict[str, Set[str]], tasks: List[Task]) -> List[Task]:
        """
        Topological sort using Kahn's algorithm
        
        Returns tasks in execution order
        """
        
        # Create task lookup
        task_map = {task.id: task for task in tasks}
        
        # Calculate in-degree for each node
        in_degree = {task_id: 0 for task_id in graph}
        for dependencies in graph.values():
            for dep in dependencies:
                if dep in in_degree:
                    in_degree[dep] += 1
        
        # Queue of nodes with no dependencies
        queue = [task_id for task_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Remove node with no dependencies
            task_id = queue.pop(0)
            result.append(task_map[task_id])
            
            # Reduce in-degree of dependent nodes
            for dependent_id in graph:
                if task_id in graph[dependent_id]:
                    in_degree[dependent_id] -= 1
                    if in_degree[dependent_id] == 0:
                        queue.append(dependent_id)
        
        # Check for cycles
        if len(result) != len(tasks):
            raise ValueError("Cyclic dependency detected in tasks")
        
        return result
    
    def _estimate_time(self, task: Task) -> int:
        """
        Estimate execution time for a task
        
        Returns: estimated time in seconds
        """
        
        # Time estimates by task type
        time_map = {
            'create_client': 2,
            'create_case': 3,
            'create_hearing': 2,
            'get_client_details': 1,
            'search_clients': 2,
            'list_all_clients': 2,
            'search_knowledge': 10,  # Knowledge search takes longer
            'analyze_case': 15,
            'draft_document': 20
        }
        
        return time_map.get(task.type, 5)  # Default: 5 seconds


__all__ = ['PlanningEngine']
