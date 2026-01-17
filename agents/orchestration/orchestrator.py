"""
Task Orchestrator
منسق المهام - ينفذ خطة التنفيذ خطوة بخطوة
"""

import logging
import asyncio
from datetime import datetime
from typing import Any, Dict
from agents.planning.task_models import ExecutionPlan, ExecutionResult, TaskStatus, ExecutionStep

logger = logging.getLogger(__name__)


class TaskOrchestrator:
    """Orchestrates task execution"""
    
    def __init__(self, unified_tools, progress_streamer=None):
        self.tools = unified_tools
        self.progress = progress_streamer
        self.context = {}  # Shared execution context
    
    async def execute_plan_async(self, plan: ExecutionPlan) -> ExecutionResult:
        """Execute plan asynchronously with progress updates"""
        
        logger.info(f"🚀 Starting plan execution: {plan.id}")
        logger.info(f"📊 {len(plan.steps)} steps, ~{plan.total_estimated_time}s")
        
        result = ExecutionResult(
            plan_id=plan.id,
            success=True,
            started_at=datetime.now()
        )
        
        try:
            for i, step in enumerate(plan.steps, 1):
                # Update step status
                step.status = TaskStatus.RUNNING
                step.started_at = datetime.now()
                
                # Send progress update
                if self.progress:
                    self.progress.update(
                        status="running",
                        message=f"⏳ {step.description}...",
                        step=i,
                        total=len(plan.steps)
                    )
                
                logger.info(f"▶️ Step {i}/{len(plan.steps)}: {step.description}")
                
                try:
                    # Execute step
                    step_result = await self._execute_step_async(step)
                    
                    # Mark as success
                    step.status = TaskStatus.SUCCESS
                    step.result = step_result
                    step.completed_at = datetime.now()
                    
                    # Store in context for dependencies
                    self.context[step.id] = step_result
                    
                    # Add to results
                    result.results.append(step_result)
                    
                    # Send success update
                    if self.progress:
                        self.progress.update(
                            status="success",
                            message=f"✅ {step.success_message}",
                            step=i,
                            total=len(plan.steps),
                            data=step_result
                        )
                    
                    logger.info(f"✅ Step {i} completed successfully")
                    
                except Exception as e:
                    # Mark as failed
                    step.status = TaskStatus.FAILED
                    step.error = str(e)
                    step.completed_at = datetime.now()
                    
                    error_msg = f"{step.error_message}: {str(e)}"
                    result.errors.append(error_msg)
                    
                    # Send error update
                    if self.progress:
                        self.progress.update(
                            status="error",
                            message=f"❌ {error_msg}",
                            step=i,
                            total=len(plan.steps)
                        )
                    
                    logger.error(f"❌ Step {i} failed: {e}")
                    
                    # Check if critical
                    if step.task.is_critical:
                        result.success = False
                        logger.error("🛑 Critical step failed, stopping execution")
                        break
                    else:
                        logger.warning("⚠️ Non-critical step failed, continuing...")
                        continue
            
            result.completed_at = datetime.now()
            
            # Send completion update
            if self.progress:
                if result.success:
                    self.progress.update(
                        status="completed",
                        message="🎉 اكتملت جميع المهام بنجاح!",
                        step=len(plan.steps),
                        total=len(plan.steps)
                    )
                else:
                    self.progress.update(
                        status="failed",
                        message=f"⚠️ فشلت بعض المهام ({len(result.errors)} خطأ)",
                        step=len(plan.steps),
                        total=len(plan.steps)
                    )
            
            logger.info(f"{'✅' if result.success else '❌'} Plan execution completed in {result.duration:.1f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Plan execution failed: {e}")
            result.success = False
            result.errors.append(str(e))
            result.completed_at = datetime.now()
            return result
    
    def execute_plan(self, plan: ExecutionPlan) -> ExecutionResult:
        """Synchronous wrapper for execute_plan_async"""
        return asyncio.run(self.execute_plan_async(plan))
    
    async def _execute_step_async(self, step: ExecutionStep) -> Any:
        """Execute a single step"""
        
        # Resolve parameter dependencies
        params = self._resolve_dependencies(step)
        
        # Execute tool
        logger.debug(f"🔧 Executing tool: {step.task.type} with params: {list(params.keys())}")
        
        # Simulate async execution (replace with actual async tools later)
        await asyncio.sleep(0.1)  # Small delay to simulate work
        
        result = self.tools.execute_tool(
            step.task.type,
            **params
        )
        
        return result
    
    def _resolve_dependencies(self, step: ExecutionStep) -> Dict[str, Any]:
        """
        Resolve parameter dependencies from context
        
        Example:
        params = {"client_id": "$task_0"}
        context = {"task_0": {"client": {"id": "abc123"}}}
        
        Returns:
        {"client_id": "abc123"}
        """
        
        params = step.task.params.copy()
        
        for key, value in params.items():
            if isinstance(value, str) and value.startswith("$"):
                # Reference to previous step result
                ref = value[1:]  # Remove $
                
                if ref in self.context:
                    # Get result from context
                    result = self.context[ref]
                    
                    # Extract ID if it's a success response with data
                    if isinstance(result, dict):
                        if 'client' in result and 'id' in result['client']:
                            params[key] = result['client']['id']
                        elif 'case' in result and 'id' in result['case']:
                            params[key] = result['case']['id']
                        elif 'id' in result:
                            params[key] = result['id']
                        else:
                            logger.warning(f"⚠️ Could not extract ID from {ref}, using full result")
                            params[key] = result
                    else:
                        params[key] = result
                else:
                    logger.warning(f"⚠️ Dependency {ref} not found in context")
        
        return params


__all__ = ['TaskOrchestrator']
