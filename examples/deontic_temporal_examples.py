"""
Usage Examples: Deontic & Temporal Logic
أمثلة عملية للمنطق الديونطي والزمني
"""

from agents.reasoning import (
    DeonticLogicSystem,
    DeonticRule,
    DeonticModality,
    TemporalLogicSystem,
    LegalDeadline
)
from datetime import datetime, timedelta


# ============================================
# Example 1: Deontic Logic - Obligations
# ============================================

def example_deontic_obligations():
    """Check legal obligations"""
    
    deontic = DeonticLogicSystem()
    
    # Check if party must honor contract
    result = deontic.check_obligation(
        subject="الطرف الأول",
        action="الوفاء بالتزامات العقد",
        context="عقد صحيح"
    )
    
    print("=" * 60)
    print("Deontic Logic - Obligations")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Reasoning: {result['reasoning']}")
    print(f"Rules: {len(result['applicable_rules'])}")
    
    # Check prohibition
    result2 = deontic.check_obligation(
        subject="الطرف الثاني",
        action="الغش",
        context=""
    )
    
    print(f"\nProhibition check: {result2['status']}")
    print(f"Reasoning: {result2['reasoning']}")


# ============================================
# Example 2: Deontic Logic - Scenario Analysis
# ============================================

def example_deontic_scenario():
    """Analyze a contract scenario"""
    
    deontic = DeonticLogicSystem()
    
    scenario = {
        "actors": ["البائع", "المشتري"],
        "actions": ["الوفاء بالعقد", "الدفع", "التسليم"],
        "context": "عقد بيع تجاري"
    }
    
    analysis = deontic.analyze_scenario(scenario)
    
    print("\n" + "=" * 60)
    print("Deontic Scenario Analysis")
    print("=" * 60)
    print(f"Obligations: {len(analysis['obligations'])}")
    print(f"Prohibitions: {len(analysis['prohibitions'])}")
    print(f"Permissions: {len(analysis['permissions'])}")
    print(f"Conflicts: {len(analysis['conflicts'])}")
    
    print("\nRecommendations:")
    for rec in analysis['recommendations']:
        print(f"  - {rec}")


# ============================================
# Example 3: Temporal Logic - Deadlines
# ============================================

def example_temporal_deadlines():
    """Track legal deadlines"""
    
    temporal = TemporalLogicSystem()
    
    # Add a deadline for appeal
    appeal_deadline = LegalDeadline(
        deadline_id="appeal_case_123",
        description="الاستئناف على الحكم رقم 123",
        due_date=datetime.now() + timedelta(days=25),
        category="appeal",
        priority="high",
        consequence="سقوط الحق في الاستئناف"
    )
    
    temporal.add_deadline(appeal_deadline)
    
    # Add a response deadline
    response_deadline = LegalDeadline(
        deadline_id="response_lawsuit_456",
        description="الرد على الدعوى رقم 456",
        due_date=datetime.now() + timedelta(days=5),
        category="response",
        priority="urgent",
        consequence="الحكم بالنكول"
    )
    
    temporal.add_deadline(response_deadline)
    
    print("\n" + "=" * 60)
    print("Temporal Logic - Deadlines")
    print("=" * 60)
    
    # Get upcoming deadlines
    upcoming = temporal.get_upcoming_deadlines(30)
    
    print(f"\nUpcoming deadlines (next 30 days): {len(upcoming)}")
    for deadline in upcoming:
        print(f"\n  📅 {deadline.description}")
        print(f"     Due: {deadline.due_date.strftime('%Y-%m-%d')}")
        print(f"     Days left: {deadline.days_remaining()}")
        print(f"     Urgency: {deadline.urgency_level()}")
        print(f"     Consequence: {deadline.consequence}")


# ============================================
# Example 4: Temporal Logic - Constraints
# ============================================

def example_temporal_constraints():
    """Check temporal constraints"""
    
    temporal = TemporalLogicSystem()
    
    # Check appeal deadline
    result = temporal.check_deadline(
        action="الاستئناف",
        reference_date=datetime.now()
    )
    
    print("\n" + "=" * 60)
    print("Temporal Constraints Check")
    print("=" * 60)
    print(f"Status: {result['status']}")
    print(f"Message: {result['message']}")
    
    if 'days_remaining' in result:
        print(f"Days remaining: {result['days_remaining']}")


# ============================================
# Example 5: Combined - Contract Analysis
# ============================================

def example_combined_contract():
    """Complete contract analysis using both systems"""
    
    print("\n" + "=" * 80)
    print("COMBINED ANALYSIS: Contract Dispute")
    print("=" * 80)
    
    # Deontic Analysis
    deontic = DeonticLogicSystem()
    
    scenario = {
        "actors": ["الطرف الأول (البائع)", "الطرف الثاني (المشتري)"],
        "actions": ["التسليم", "الدفع", "فسخ العقد"],
        "context": "عقد بيع مع تأخر في التسليم"
    }
    
    deontic_analysis = deontic.analyze_scenario(scenario)
    
    print("\n📊 Deontic Analysis:")
    print(f"  - Obligations: {len(deontic_analysis['obligations'])}")
    print(f"  - Prohibitions: {len(deontic_analysis['prohibitions'])}")
    
    # Temporal Analysis
    temporal = TemporalLogicSystem()
    
    # Create deadline from constraint
    delivery_deadline = temporal.create_deadline_from_constraint(
        constraint_id="lawsuit_response",
        description="الموعد النهائي للرد على دعوى التأخير",
        start_date=datetime.now(),
        category="response"
    )
    
    print("\n📅 Temporal Analysis:")
    if delivery_deadline:
        print(f"  - Deadline created: {delivery_deadline.description}")
        print(f"  - Due date: {delivery_deadline.due_date.strftime('%Y-%m-%d')}")
        print(f"  - Days remaining: {delivery_deadline.days_remaining()}")
        print(f"  - Urgency: {delivery_deadline.urgency_level()}")
    
    # Combined recommendations
    print("\n💡 Combined Recommendations:")
    for rec in deontic_analysis['recommendations']:
        print(f"  ✓ {rec}")
    
    if delivery_deadline and delivery_deadline.days_remaining() < 7:
        print(f"  ⚠️ عاجل: يجب الرد خلال {delivery_deadline.days_remaining()} أيام")


# ============================================
# Example 6: Statistics
# ============================================

def example_stats():
    """Get system statistics"""
    
    deontic = DeonticLogicSystem()
    temporal = TemporalLogicSystem()
    
    print("\n" + "=" * 60)
    print("System Statistics")
    print("=" * 60)
    
    deontic_stats = deontic.get_stats()
    print("\nDeontic Logic:")
    print(f"  Total rules: {deontic_stats['total_rules']}")
    print(f"  By modality: {deontic_stats['by_modality']}")
    
    temporal_stats = temporal.get_stats()
    print("\nTemporal Logic:")
    print(f"  Total constraints: {temporal_stats['total_constraints']}")
    print(f"  Total deadlines: {temporal_stats['total_deadlines']}")
    print(f"  Upcoming: {temporal_stats['upcoming_deadlines']}")
    print(f"  Overdue: {temporal_stats['overdue_deadlines']}")


# ============================================
# Run All Examples
# ============================================

if __name__ == "__main__":
    print("=" * 80)
    print("DEONTIC & TEMPORAL LOGIC EXAMPLES")
    print("=" * 80)
    
    example_deontic_obligations()
    example_deontic_scenario()
    example_temporal_deadlines()
    example_temporal_constraints()
    example_combined_contract()
    example_stats()
    
    print("\n" + "=" * 80)
    print("✅ All examples completed!")
    print("=" * 80)
