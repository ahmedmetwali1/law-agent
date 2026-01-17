"""
Deontic Logic System
نظام المنطق الديونطي

Handles:
- Obligations (الواجبات) - ◯
- Prohibitions (المحظورات) - F
- Permissions (المباح) - ◇
- Commissions (الأوامر)
- Omissions (النواهي)

Based on modal logic for normative reasoning
Perfect for legal systems!
"""

from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DeonticModality(str, Enum):
    """Deontic modalities"""
    OBLIGATORY = "obligatory"      # واجب (◯)
    FORBIDDEN = "forbidden"        # محظور (F)
    PERMITTED = "permitted"        # مباح (◇)
    OPTIONAL = "optional"          # اختياري
    SUPEREROGATORY = "supererogatory"  # مستحب (beyond duty)


class DeonticOperator(str, Enum):
    """Deontic operators (symbols)"""
    OB = "◯"    # Obligatory
    PER = "◇"   # Permitted
    FOR = "F"   # Forbidden


@dataclass
class DeonticRule:
    """A deontic rule expressing normative statement"""
    rule_id: str
    modality: DeonticModality
    subject: str          # من يجب عليه
    action: str           # ما يجب فعله
    context: str = ""     # في أي سياق
    exceptions: List[str] = None
    source: str = ""      # مصدر القاعدة
    priority: int = 0     # Priority (higher = more important)
    
    def __post_init__(self):
        if self.exceptions is None:
            self.exceptions = []
    
    def to_formula(self) -> str:
        """Convert to deontic logic formula"""
        operator = {
            DeonticModality.OBLIGATORY: DeonticOperator.OB.value,
            DeonticModality.FORBIDDEN: DeonticOperator.FOR.value,
            DeonticModality.PERMITTED: DeonticOperator.PER.value
        }.get(self.modality, "?")
        
        return f"{operator}({self.subject}: {self.action})"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "modality": self.modality.value,
            "subject": self.subject,
            "action": self.action,
            "context": self.context,
            "exceptions": self.exceptions,
            "source": self.source,
            "priority": self.priority,
            "formula": self.to_formula()
        }


class DeonticConflict:
    """Represents a conflict between deontic rules"""
    def __init__(
        self,
        rule1: DeonticRule,
        rule2: DeonticRule,
        conflict_type: str
    ):
        self.rule1 = rule1
        self.rule2 = rule2
        self.conflict_type = conflict_type  # "obligation_prohibition", etc.


class DeonticLogicSystem:
    """
    Complete Deontic Logic System
    
    Handles normative reasoning for legal obligations
    """
    
    def __init__(self):
        self.rules: Dict[str, DeonticRule] = {}
        self.conflicts: List[DeonticConflict] = []
        
        # Initialize Saudi legal rules
        self._initialize_saudi_law()
        
        logger.info("✅ Deontic Logic System initialized")
    
    def _initialize_saudi_law(self):
        """Initialize common Saudi legal obligations"""
        
        # Obligation: Contract parties must honor agreements
        self.add_rule(DeonticRule(
            rule_id="contract_honor",
            modality=DeonticModality.OBLIGATORY,
            subject="أطراف العقد",
            action="الوفاء بالتزامات العقد",
            context="عقد صحيح",
            source="نظام المعاملات المدنية"
        ))
        
        # Prohibition: No fraud in contracts
        self.add_rule(DeonticRule(
            rule_id="no_fraud",
            modality=DeonticModality.FORBIDDEN,
            subject="أطراف العقد",
            action="الغش أو التدليس",
            context="في جميع المعاملات",
            source="الأنظمة التجارية"
        ))
        
        # Permission: Right to terminate under conditions
        self.add_rule(DeonticRule(
            rule_id="termination_right",
            modality=DeonticModality.PERMITTED,
            subject="الطرف المتضرر",
            action="فسخ العقد",
            context="عند الإخلال الجوهري",
            source="نظام المعاملات المدنية"
        ))
        
        # Obligation: Proof burden on claimant
        self.add_rule(DeonticRule(
            rule_id="burden_of_proof",
            modality=DeonticModality.OBLIGATORY,
            subject="المدعي",
            action="إثبات ادعائه",
            context="في جميع الدعاوى",
            source="نظام المرافعات - البينة على من ادعى",
            priority=10
        ))
        
        logger.info(f"Loaded {len(self.rules)} deontic rules")
    
    def add_rule(self, rule: DeonticRule) -> None:
        """Add a deontic rule"""
        self.rules[rule.rule_id] = rule
        logger.debug(f"Added deontic rule: {rule.to_formula()}")
    
    def check_obligation(
        self,
        subject: str,
        action: str,
        context: str = ""
    ) -> Dict[str, Any]:
        """
        Check if subject is obligated to perform action
        
        Returns:
            obligation_status with reasoning
        """
        logger.info(f"Checking obligation: {subject} - {action}")
        
        # Find relevant rules
        relevant_rules = []
        for rule in self.rules.values():
            if (subject.lower() in rule.subject.lower() or 
                action.lower() in rule.action.lower()):
                relevant_rules.append(rule)
        
        # Check for obligations
        obligations = [
            r for r in relevant_rules
            if r.modality == DeonticModality.OBLIGATORY
        ]
        
        # Check for prohibitions
        prohibitions = [
            r for r in relevant_rules
            if r.modality == DeonticModality.FORBIDDEN
        ]
        
        # Determine result
        if obligations:
            status = "obligatory"
            reasoning = f"يجب على {subject} {action}"
            applicable_rules = obligations
        elif prohibitions:
            status = "forbidden"
            reasoning = f"محظور على {subject} {action}"
            applicable_rules = prohibitions
        else:
            # Check permissions
            permissions = [
                r for r in relevant_rules
                if r.modality == DeonticModality.PERMITTED
            ]
            if permissions:
                status = "permitted"
                reasoning = f"يجوز لـ {subject} {action}"
                applicable_rules = permissions
            else:
                status = "unspecified"
                reasoning = "لا توجد قاعدة واضحة"
                applicable_rules = []
        
        return {
            "status": status,
            "reasoning": reasoning,
            "applicable_rules": [r.to_dict() for r in applicable_rules],
            "conflicts": self._check_conflicts(applicable_rules)
        }
    
    def _check_conflicts(self, rules: List[DeonticRule]) -> List[Dict[str, Any]]:
        """Check for conflicts between rules"""
        conflicts = []
        
        for i, rule1 in enumerate(rules):
            for rule2 in rules[i+1:]:
                # Check for obligation-prohibition conflict
                if (rule1.modality == DeonticModality.OBLIGATORY and
                    rule2.modality == DeonticModality.FORBIDDEN):
                    conflicts.append({
                        "type": "obligation_prohibition",
                        "rule1": rule1.rule_id,
                        "rule2": rule2.rule_id,
                        "severity": "high"
                    })
                
                # Check for same action different modalities
                if (rule1.action.lower() == rule2.action.lower() and
                    rule1.modality != rule2.modality):
                    conflicts.append({
                        "type": "modality_conflict",
                        "rule1": rule1.rule_id,
                        "rule2": rule2.rule_id,
                        "severity": "medium"
                    })
        
        return conflicts
    
    def resolve_conflict(
        self,
        rule1: DeonticRule,
        rule2: DeonticRule
    ) -> DeonticRule:
        """
        Resolve conflict between two rules
        
        Resolution strategies:
        1. Priority-based (lex superior)
        2. Specificity-based (lex specialis)
        3. Temporal-based (lex posterior)
        """
        # Strategy 1: Priority
        if rule1.priority > rule2.priority:
            logger.info(f"Resolved by priority: {rule1.rule_id} wins")
            return rule1
        elif rule2.priority > rule1.priority:
            logger.info(f"Resolved by priority: {rule2.rule_id} wins")
            return rule2
        
        # Strategy 2: Specificity (more context = more specific)
        if len(rule1.context) > len(rule2.context):
            logger.info(f"Resolved by specificity: {rule1.rule_id} wins")
            return rule1
        elif len(rule2.context) > len(rule1.context):
            logger.info(f"Resolved by specificity: {rule2.rule_id} wins")
            return rule2
        
        # Default: First rule
        logger.warning("No clear resolution - defaulting to first rule")
        return rule1
    
    def derive_implications(self, rule: DeonticRule) -> List[DeonticRule]:
        """
        Derive logical implications from a rule
        
        Examples:
        - If ◯(pay) then ¬F(pay) (obligatory implies not forbidden)
        - If F(kill) then ¬◯(kill) (forbidden implies not obligatory)
        """
        implications = []
        
        if rule.modality == DeonticModality.OBLIGATORY:
            # Obligatory implies permitted
            implications.append(DeonticRule(
                rule_id=f"{rule.rule_id}_implied_permission",
                modality=DeonticModality.PERMITTED,
                subject=rule.subject,
                action=rule.action,
                context=rule.context,
                source=f"Derived from {rule.rule_id}"
            ))
        
        elif rule.modality == DeonticModality.FORBIDDEN:
            # Forbidden implies not obligatory (in normal context)
            pass  # Already covered by conflict detection
        
        return implications
    
    def analyze_scenario(
        self,
        scenario: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze a legal scenario using deontic logic
        
        Args:
            scenario: {
                "actors": ["party1", "party2"],
                "actions": ["pay", "deliver"],
                "context": "contract dispute"
            }
        
        Returns:
            Complete deontic analysis
        """
        logger.info("🔍 Analyzing scenario with deontic logic")
        
        analysis = {
            "scenario": scenario,
            "obligations": [],
            "prohibitions": [],
            "permissions": [],
            "conflicts": [],
            "recommendations": []
        }
        
        # Analyze each actor-action pair
        for actor in scenario.get("actors", []):
            for action in scenario.get("actions", []):
                result = self.check_obligation(
                    subject=actor,
                    action=action,
                    context=scenario.get("context", "")
                )
                
                if result["status"] == "obligatory":
                    analysis["obligations"].append(result)
                elif result["status"] == "forbidden":
                    analysis["prohibitions"].append(result)
                elif result["status"] == "permitted":
                    analysis["permissions"].append(result)
                
                # Collect conflicts
                analysis["conflicts"].extend(result.get("conflicts", []))
        
        # Generate recommendations
        analysis["recommendations"] = self._generate_recommendations(analysis)
        
        logger.info(f"Analysis complete: {len(analysis['obligations'])} obligations found")
        return analysis
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate legal recommendations based on analysis"""
        recommendations = []
        
        if analysis["obligations"]:
            recommendations.append(
                f"يجب الالتزام بـ {len(analysis['obligations'])} واجب قانوني"
            )
        
        if analysis["prohibitions"]:
            recommendations.append(
                f"تجنب {len(analysis['prohibitions'])} محظورات"
            )
        
        if analysis["conflicts"]:
            recommendations.append(
                f"⚠️ يوجد {len(analysis['conflicts'])} تعارض يحتاج حل"
            )
        
        return recommendations
    
    def get_stats(self) -> Dict[str, Any]:
        """Get system statistics"""
        modality_counts = {}
        for rule in self.rules.values():
            modality = rule.modality.value
            modality_counts[modality] = modality_counts.get(modality, 0) + 1
        
        return {
            "total_rules": len(self.rules),
            "by_modality": modality_counts,
            "conflicts_detected": len(self.conflicts)
        }


__all__ = [
    "DeonticLogicSystem",
    "DeonticRule",
    "DeonticModality",
    "DeonticOperator",
    "DeonticConflict"
]
