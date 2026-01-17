"""
Temporal Logic System
نظام المنطق الزمني

Handles:
- Always (G) - دائماً
- Eventually (F) - في النهاية
- Next (X) - التالي
- Until (U) - حتى
- Legal deadlines and time constraints
- Prescription periods (التقادم)

Based on Linear Temporal Logic (LTL)
Essential for legal time tracking!
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class TemporalOperator(str, Enum):
    """Temporal operators"""
    ALWAYS = "G"           # Globally (always) - دائماً
    EVENTUALLY = "F"       # Finally (eventually) - في النهاية
    NEXT = "X"             # Next - التالي
    UNTIL = "U"            # Until - حتى
    SINCE = "S"            # Since - منذ
    BEFORE = "B"           # Before - قبل
    AFTER = "A"            # After - بعد


class TimeUnit(str, Enum):
    """Time units"""
    DAYS = "days"
    WEEKS = "weeks"
    MONTHS = "months"
    YEARS = "years"
    HOURS = "hours"


@dataclass
class TemporalConstraint:
    """A temporal constraint on legal actions"""
    constraint_id: str
    operator: TemporalOperator
    condition: str
    duration: Optional[int] = None
    unit: Optional[TimeUnit] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: str = ""
    source: str = ""
    
    def to_formula(self) -> str:
        """Convert to temporal logic formula"""
        if self.duration and self.unit:
            return f"{self.operator.value}[{self.duration} {self.unit.value}]({self.condition})"
        return f"{self.operator.value}({self.condition})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "constraint_id": self.constraint_id,
            "operator": self.operator.value,
            "condition": self.condition,
            "duration": self.duration,
            "unit": self.unit.value if self.unit else None,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "description": self.description,
            "formula": self.to_formula()
        }


@dataclass
class LegalDeadline:
    """A legal deadline"""
    deadline_id: str
    description: str
    due_date: datetime
    category: str  # "filing", "response", "appeal", etc.
    priority: str = "normal"  # "low", "normal", "high", "urgent"
    consequence: str = ""  # What happens if missed
    source: str = ""
    
    def days_remaining(self) -> int:
        """Calculate days remaining"""
        delta = self.due_date - datetime.now()
        return delta.days
    
    def is_overdue(self) -> bool:
        """Check if deadline passed"""
        return datetime.now() > self.due_date
    
    def urgency_level(self) -> str:
        """Calculate urgency level"""
        days = self.days_remaining()
        
        if days < 0:
            return "overdue"
        elif days <= 3:
            return "critical"
        elif days <= 7:
            return "urgent"
        elif days <= 14:
            return "soon"
        else:
            return "normal"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "deadline_id": self.deadline_id,
            "description": self.description,
            "due_date": self.due_date.isoformat(),
            "days_remaining": self.days_remaining(),
            "is_overdue": self.is_overdue(),
            "urgency": self.urgency_level(),
            "category": self.category,
            "priority": self.priority,
            "consequence": self.consequence
        }


class TemporalLogicSystem:
    """
    Complete Temporal Logic System
    
    Tracks legal deadlines, time constraints, and temporal relationships
    """
    
    def __init__(self):
        self.constraints: Dict[str, TemporalConstraint] = {}
        self.deadlines: Dict[str, LegalDeadline] = {}
        
        # Initialize Saudi legal time limits
        self._initialize_saudi_time_limits()
        
        logger.info("✅ Temporal Logic System initialized")
    
    def _initialize_saudi_time_limits(self):
        """Initialize common Saudi legal time limits"""
        
        # Appeal period
        self.add_constraint(TemporalConstraint(
            constraint_id="appeal_period",
            operator=TemporalOperator.UNTIL,
            condition="يجوز الاستئناف",
            duration=30,
            unit=TimeUnit.DAYS,
            description="مدة الاستئناف",
            source="نظام المرافعات الشرعية"
        ))
        
        # Response to lawsuit
        self.add_constraint(TemporalConstraint(
            constraint_id="lawsuit_response",
            operator=TemporalOperator.UNTIL,
            condition="الرد على الدعوى",
            duration=15,
            unit=TimeUnit.DAYS,
            description="مدة الرد على الدعوى",
            source="نظام المرافعات"
        ))
        
        # Contract prescription (general)
        self.add_constraint(TemporalConstraint(
            constraint_id="contract_prescription",
            operator=TemporalOperator.UNTIL,
            condition="سقوط الحق بالتقادم",
            duration=10,
            unit=TimeUnit.YEARS,
            description="مدة التقادم العامة للعقود",
            source="نظام المعاملات المدنية"
        ))
        
        # Cancellation period (consumer protection)
        self.add_constraint(TemporalConstraint(
            constraint_id="consumer_cancellation",
            operator=TemporalOperator.UNTIL,
            condition="حق الإلغاء للمستهلك",
            duration=7,
            unit=TimeUnit.DAYS,
            description="فترة التراجع للمستهلك",
            source="نظام حماية المستهلك"
        ))
        
        logger.info(f"Loaded {len(self.constraints)} temporal constraints")
    
    def add_constraint(self, constraint: TemporalConstraint) -> None:
        """Add a temporal constraint"""
        self.constraints[constraint.constraint_id] = constraint
        logger.debug(f"Added temporal constraint: {constraint.to_formula()}")
    
    def add_deadline(self, deadline: LegalDeadline) -> None:
        """Add a legal deadline"""
        self.deadlines[deadline.deadline_id] = deadline
        logger.info(f"Added deadline: {deadline.description} - {deadline.days_remaining()} days remaining")
    
    def check_deadline(
        self,
        action: str,
        reference_date: datetime = None
    ) -> Dict[str, Any]:
        """
        Check if action is within deadline
        
        Args:
            action: Action to check
            reference_date: Reference date (default: now)
        
        Returns:
            Deadline status
        """
        if reference_date is None:
            reference_date = datetime.now()
        
        logger.info(f"Checking deadline for: {action}")
        
        # Find relevant constraints
        relevant = []
        for constraint in self.constraints.values():
            if action.lower() in constraint.condition.lower():
                relevant.append(constraint)
        
        if not relevant:
            return {
                "status": "no_constraint",
                "message": "لا توجد قيود زمنية محددة"
            }
        
        # Calculate deadline
        constraint = relevant[0]  # Take first match
        
        if constraint.duration and constraint.unit:
            # Calculate end date
            if constraint.start_date:
                start = constraint.start_date
            else:
                start = reference_date
            
            delta = self._calculate_timedelta(constraint.duration, constraint.unit)
            end_date = start + delta
            
            days_left = (end_date - reference_date).days
            
            return {
                "status": "within_deadline" if days_left > 0 else "overdue",
                "constraint": constraint.to_dict(),
                "end_date": end_date.isoformat(),
                "days_remaining": days_left,
                "message": f"المدة المتبقية: {days_left} يوم"
            }
        
        return {
            "status": "unknown",
            "constraint": constraint.to_dict()
        }
    
    def _calculate_timedelta(self, duration: int, unit: TimeUnit) -> timedelta:
        """Calculate timedelta from duration and unit"""
        if unit == TimeUnit.DAYS:
            return timedelta(days=duration)
        elif unit == TimeUnit.WEEKS:
            return timedelta(weeks=duration)
        elif unit == TimeUnit.MONTHS:
            return timedelta(days=duration * 30)  # Approximate
        elif unit == TimeUnit.YEARS:
            return timedelta(days=duration * 365)  # Approximate
        elif unit == TimeUnit.HOURS:
            return timedelta(hours=duration)
        else:
            return timedelta(days=duration)
    
    def get_upcoming_deadlines(self, days_ahead: int = 30) -> List[LegalDeadline]:
        """Get all deadlines in next N days"""
        upcoming = []
        cutoff = datetime.now() + timedelta(days=days_ahead)
        
        for deadline in self.deadlines.values():
            if not deadline.is_overdue() and deadline.due_date <= cutoff:
                upcoming.append(deadline)
        
        # Sort by due date
        upcoming.sort(key=lambda d: d.due_date)
        
        logger.info(f"Found {len(upcoming)} upcoming deadlines")
        return upcoming
    
    def get_overdue_deadlines(self) -> List[LegalDeadline]:
        """Get all overdue deadlines"""
        overdue = [d for d in self.deadlines.values() if d.is_overdue()]
        overdue.sort(key=lambda d: d.due_date, reverse=True)
        
        logger.info(f"Found {len(overdue)} overdue deadlines")
        return overdue
    
    def create_deadline_from_constraint(
        self,
        constraint_id: str,
        description: str,
        start_date: datetime = None,
        category: str = "general"
    ) -> Optional[LegalDeadline]:
        """Create a deadline from a temporal constraint"""
        constraint = self.constraints.get(constraint_id)
        
        if not constraint:
            logger.error(f"Constraint '{constraint_id}' not found")
            return None
        
        if not constraint.duration or not constraint.unit:
            logger.error("Constraint must have duration and unit")
            return None
        
        if start_date is None:
            start_date = datetime.now()
        
        delta = self._calculate_timedelta(constraint.duration, constraint.unit)
        due_date = start_date + delta
        
        deadline = LegalDeadline(
            deadline_id=f"{constraint_id}_{int(start_date.timestamp())}",
            description=description,
            due_date=due_date,
            category=category,
            consequence=f"انتهاء مدة: {constraint.description}",
            source=constraint.source
        )
        
        self.add_deadline(deadline)
        return deadline
    
    def analyze_temporal_sequence(
        self,
        events: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Analyze a sequence of events temporally
        
        Args:
            events: List of {"name": str, "date": datetime}
        
        Returns:
            Temporal analysis
        """
        logger.info(f"Analyzing temporal sequence of {len(events)} events")
        
        # Sort by date
        sorted_events = sorted(events, key=lambda e: e["date"])
        
        analysis = {
            "total_events": len(events),
            "first_event": sorted_events[0] if sorted_events else None,
            "last_event": sorted_events[-1] if sorted_events else None,
            "duration": None,
            "gaps": [],
            "violations": []
        }
        
        if len(sorted_events) >= 2:
            duration = sorted_events[-1]["date"] - sorted_events[0]["date"]
            analysis["duration"] = {
                "days": duration.days,
                "description": f"{duration.days} يوم"
            }
            
            # Check for gaps
            for i in range(len(sorted_events) - 1):
                gap = sorted_events[i+1]["date"] - sorted_events[i]["date"]
                if gap.days > 90:  # Large gap
                    analysis["gaps"].append({
                        "between": [sorted_events[i]["name"], sorted_events[i+1]["name"]],
                        "days": gap.days
                    })
        
        # Check for deadline violations
        for event in events:
            event_name = event.get("name", "")
            event_date = event.get("date")
            
            deadline_check = self.check_deadline(event_name, event_date)
            if deadline_check.get("status") == "overdue":
                analysis["violations"].append({
                    "event": event_name,
                    "date": event_date.isoformat(),
                    "constraint": deadline_check.get("constraint")
                })
        
        return analysis
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        return {
            "total_constraints": len(self.constraints),
            "total_deadlines": len(self.deadlines),
            "upcoming_deadlines": len(self.get_upcoming_deadlines(30)),
            "overdue_deadlines": len(self.get_overdue_deadlines()),
            "constraints_by_operator": self._count_by_operator()
        }
    
    def _count_by_operator(self) -> Dict[str, int]:
        """Count constraints by operator"""
        counts = {}
        for constraint in self.constraints.values():
            op = constraint.operator.value
            counts[op] = counts.get(op, 0) + 1
        return counts


__all__ = [
    "TemporalLogicSystem",
    "TemporalConstraint",
    "LegalDeadline",
    "TemporalOperator",
    "TimeUnit"
]
