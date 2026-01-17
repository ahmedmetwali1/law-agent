"""
Plan Tracker Tool
أداة تتبع الخطوات والخطط

تتيح للوكيل إنشاء خطة خطوة بخطوة وتتبع تنفيذها
وإخراجها كـ JSON لعرضها في واجهة المستخدم
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class StepStatus(Enum):
    """حالات الخطوة"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class PlanStep:
    """خطوة في الخطة"""
    id: int
    title: str
    description: str
    status: StepStatus = StepStatus.PENDING
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    result: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى dictionary"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status.value,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "result": self.result,
            "error": self.error
        }
    
    def start(self):
        """بدء الخطوة"""
        self.status = StepStatus.IN_PROGRESS
        self.started_at = datetime.now().isoformat()
        logger.info(f"▶️ بدء الخطوة {self.id}: {self.title}")
    
    def complete(self, result: str = None):
        """إكمال الخطوة"""
        self.status = StepStatus.COMPLETED
        self.completed_at = datetime.now().isoformat()
        self.result = result
        logger.info(f"✅ اكتملت الخطوة {self.id}: {self.title}")
    
    def fail(self, error: str):
        """فشل الخطوة"""
        self.status = StepStatus.FAILED
        self.completed_at = datetime.now().isoformat()
        self.error = error
        logger.error(f"❌ فشلت الخطوة {self.id}: {self.title} - {error}")


@dataclass
class ExecutionPlan:
    """خطة التنفيذ الكاملة"""
    id: str
    title: str
    description: str
    steps: List[PlanStep] = field(default_factory=list)
    status: str = "in_progress"
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    def add_step(self, title: str, description: str) -> PlanStep:
        """إضافة خطوة جديدة"""
        step_id = len(self.steps) + 1
        step = PlanStep(
            id=step_id,
            title=title,
            description=description
        )
        self.steps.append(step)
        logger.info(f"➕ أضيفت خطوة {step_id}: {title}")
        return step
    
    def get_step(self, step_id: int) -> Optional[PlanStep]:
        """الحصول على خطوة بالـ ID"""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_current_step(self) -> Optional[PlanStep]:
        """الحصول على الخطوة الحالية (أول pending أو in_progress)"""
        for step in self.steps:
            if step.status in [StepStatus.PENDING, StepStatus.IN_PROGRESS]:
                return step
        return None
    
    def mark_completed(self):
        """تحديد الخطة كمكتملة"""
        self.status = "completed"
        self.completed_at = datetime.now().isoformat()
        logger.info(f"🎉 اكتملت الخطة: {self.title}")
    
    def to_json(self, indent: int = 2) -> str:
        """تحويل إلى JSON"""
        data = {
            "plan_id": self.id,
            "title": self.title,
            "description": self.description,
            "status": self.status,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "total_steps": len(self.steps),
            "completed_steps": sum(1 for s in self.steps if s.status == StepStatus.COMPLETED),
            "steps": [step.to_dict() for step in self.steps]
        }
        return json.dumps(data, ensure_ascii=False, indent=indent)
    
    def to_dict(self) -> Dict[str, Any]:
        """تحويل إلى dictionary"""
        return json.loads(self.to_json())


class PlanTrackerTool:
    """
    أداة تتبع الخطط
    
    تستخدم لإنشاء خطط خطوة بخطوة وتتبع تنفيذها
    """
    
    def __init__(self):
        self.current_plan: Optional[ExecutionPlan] = None
        logger.info("📋 تم تهيئة أداة تتبع الخطط")
    
    def create_plan(
        self,
        plan_id: str,
        title: str,
        description: str,
        steps: List[Dict[str, str]]
    ) -> str:
        """
        إنشاء خطة جديدة
        
        Args:
            plan_id: معرف الخطة
            title: عنوان الخطة
            description: وصف الخطة
            steps: قائمة الخطوات [{"title": "...", "description": "..."}]
            
        Returns:
            JSON للخطة
        """
        logger.info(f"📝 إنشاء خطة جديدة: {title}")
        
        self.current_plan = ExecutionPlan(
            id=plan_id,
            title=title,
            description=description
        )
        
        # إضافة الخطوات
        for step_data in steps:
            self.current_plan.add_step(
                title=step_data.get("title", ""),
                description=step_data.get("description", "")
            )
        
        logger.info(f"✅ تم إنشاء خطة بـ {len(steps)} خطوات")
        return self.current_plan.to_json()
    
    def start_step(self, step_id: int) -> str:
        """
        بدء خطوة معينة
        
        Args:
            step_id: رقم الخطوة
            
        Returns:
            JSON للخطة المحدثة
        """
        if not self.current_plan:
            raise ValueError("لا توجد خطة نشطة")
        
        step = self.current_plan.get_step(step_id)
        if not step:
            raise ValueError(f"الخطوة {step_id} غير موجودة")
        
        step.start()
        return self.current_plan.to_json()
    
    def complete_step(self, step_id: int, result: str = None) -> str:
        """
        إكمال خطوة معينة
        
        Args:
            step_id: رقم الخطوة
            result: نتيجة الخطوة (اختياري)
            
        Returns:
            JSON للخطة المحدثة
        """
        if not self.current_plan:
            raise ValueError("لا توجد خطة نشطة")
        
        step = self.current_plan.get_step(step_id)
        if not step:
            raise ValueError(f"الخطوة {step_id} غير موجودة")
        
        step.complete(result)
        return self.current_plan.to_json()
    
    def fail_step(self, step_id: int, error: str) -> str:
        """
        تحديد فشل خطوة
        
        Args:
            step_id: رقم الخطوة
            error: رسالة الخطأ
            
        Returns:
            JSON للخطة المحدثة
        """
        if not self.current_plan:
            raise ValueError("لا توجد خطة نشطة")
        
        step = self.current_plan.get_step(step_id)
        if not step:
            raise ValueError(f"الخطوة {step_id} غير موجودة")
        
        step.fail(error)
        return self.current_plan.to_json()
    
    def get_current_plan_json(self) -> str:
        """
        الحصول على الخطة الحالية كـ JSON
        
        Returns:
            JSON للخطة الحالية
        """
        if not self.current_plan:
            return json.dumps({"error": "لا توجد خطة نشطة"}, ensure_ascii=False)
        
        return self.current_plan.to_json()
    
    def mark_plan_completed(self) -> str:
        """
        تحديد الخطة كمكتملة
        
        Returns:
            JSON للخطة المكتملة
        """
        if not self.current_plan:
            raise ValueError("لا توجد خطة نشطة")
        
        self.current_plan.mark_completed()
        return self.current_plan.to_json()
    
    def get_plan_summary(self) -> Dict[str, Any]:
        """
        الحصول على ملخص الخطة
        
        Returns:
            ملخص الخطة
        """
        if not self.current_plan:
            return {"error": "لا توجد خطة نشطة"}
        
        return {
            "plan_id": self.current_plan.id,
            "title": self.current_plan.title,
            "status": self.current_plan.status,
            "progress": f"{sum(1 for s in self.current_plan.steps if s.status == StepStatus.COMPLETED)}/{len(self.current_plan.steps)}",
            "current_step": self.current_plan.get_current_step().title if self.current_plan.get_current_step() else "لا توجد"
        }


# مثال على الاستخدام
if __name__ == "__main__":
    # إنشاء أداة التتبع
    tracker = PlanTrackerTool()
    
    # إنشاء خطة
    plan_json = tracker.create_plan(
        plan_id="case_001",
        title="معالجة قضية جديدة",
        description="تحليل ومعالجة قضية العميل الجديد",
        steps=[
            {"title": "استقبال الوقائع", "description": "جمع جميع المعلومات من العميل"},
            {"title": "التحليل الأولي", "description": "تحليل نوع القضية والنقاط القانونية"},
            {"title": "البحث القانوني", "description": "البحث عن المواد والسوابق ذات الصلة"},
            {"title": "إعداد الخطة", "description": "وضع استراتيجية قانونية"},
            {"title": "التقرير النهائي", "description": "إعداد تقرير شامل للعميل"}
        ]
    )
    
    print("=" * 60)
    print("📋 الخطة المُنشأة:")
    print("=" * 60)
    print(plan_json)
    
    # بدء وإكمال الخطوات
    print("\n" + "=" * 60)
    print("⚙️ تنفيذ الخطوات:")
    print("=" * 60)
    
    tracker.start_step(1)
    tracker.complete_step(1, "تم استقبال الوقائع بنجاح")
    
    tracker.start_step(2)
    tracker.complete_step(2, "القضية مدنية - نزاع عقد")
    
    tracker.start_step(3)
    print("\n📊 الخطة المحدثة:")
    print(tracker.get_current_plan_json())
    
    # ملخص
    print("\n" + "=" * 60)
    print("📈 ملخص التقدم:")
    print("=" * 60)
    print(json.dumps(tracker.get_plan_summary(), ensure_ascii=False, indent=2))


__all__ = ["PlanTrackerTool", "ExecutionPlan", "PlanStep", "StepStatus"]
