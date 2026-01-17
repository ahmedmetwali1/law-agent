"""
Neural-Symbolic Reasoning Engine
محرك التفكير العصبي-الرمزي للمنطق القانوني

Combines:
- Neural Networks (LLM) for pattern recognition
- Symbolic Logic for legal reasoning
- Rule-based inference for guaranteed correctness

Based on 2025 research on hybrid AI systems
"""

from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class LogicOperator(str, Enum):
    """Logical operators"""
    AND = "∧"
    OR = "∨"
    NOT = "¬"
    IMPLIES = "→"
    IFF = "↔"  # if and only if


class RuleType(str, Enum):
    """Types of legal rules"""
    CONDITION = "condition"           # إذا... فإن
    PROHIBITION = "prohibition"       # محظور
    OBLIGATION = "obligation"         # واجب
    PERMISSION = "permission"         # مباح
    EXCEPTION = "exception"           # استثناء
    DEFINITION = "definition"         # تعريف


@dataclass
class LegalRule:
    """Represents a legal rule in symbolic form"""
    rule_id: str
    rule_type: RuleType
    condition: str  # Logical expression
    conclusion: str  # What follows
    confidence: float = 1.0
    source: str = ""
    exceptions: List[str] = None
    
    def __post_init__(self):
        if self.exceptions is None:
            self.exceptions = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "rule_id": self.rule_id,
            "type": self.rule_type.value,
            "condition": self.condition,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "source": self.source,
            "exceptions": self.exceptions
        }


@dataclass
class LogicalFact:
    """A proven or assumed fact"""
    fact_id: str
    statement: str
    certainty: float = 1.0  # 0.0 to 1.0
    source: str = "given"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "fact_id": self.fact_id,
            "statement": self.statement,
            "certainty": self.certainty,
            "source": self.source
        }


class NeuralSymbolicReasoning:
    """
    Neural-Symbolic Reasoning Engine
    
    Combines:
    - LLM (neural) for understanding natural language
    - Symbolic logic for rigorous legal reasoning
    """
    
    def __init__(self, llm_agent=None):
        self.llm = llm_agent
        
        # Knowledge base
        self.rules: Dict[str, LegalRule] = {}
        self.facts: Dict[str, LogicalFact] = {}
        
        # Inference chain
        self.inference_history: List[Dict[str, Any]] = []
        
        # Built-in legal rules (Saudi law examples)
        self._initialize_legal_rules()
        
        logger.info("✅ Neural-Symbolic Reasoning Engine initialized")
    
    def _initialize_legal_rules(self):
        """Initialize common legal rules"""
        
        # Rule 1: Contract validity
        self.add_rule(LegalRule(
            rule_id="contract_validity_1",
            rule_type=RuleType.CONDITION,
            condition="(offer ∧ acceptance ∧ consideration ∧ capacity ∧ legality)",
            conclusion="valid_contract",
            confidence=1.0,
            source="Saudi Contract Law"
        ))
        
        # Rule 2: Burden of proof
        self.add_rule(LegalRule(
            rule_id="burden_of_proof",
            rule_type=RuleType.OBLIGATION,
            condition="claims_right",
            conclusion="must_prove",
            confidence=1.0,
            source="Evidence Law - البينة على من ادعى"
        ))
        
        # Rule 3: Good faith requirement
        self.add_rule(LegalRule(
            rule_id="good_faith",
            rule_type=RuleType.OBLIGATION,
            condition="contractual_relationship",
            conclusion="must_act_in_good_faith",
            confidence=1.0,
            source="Saudi Contract Law"
        ))
        
        logger.info(f"Loaded {len(self.rules)} legal rules")
    
    def add_rule(self, rule: LegalRule) -> None:
        """Add a legal rule to knowledge base"""
        self.rules[rule.rule_id] = rule
        logger.debug(f"Added rule: {rule.rule_id}")
    
    def add_fact(self, fact: LogicalFact) -> None:
        """Add a fact to knowledge base"""
        self.facts[fact.fact_id] = fact
        logger.debug(f"Added fact: {fact.fact_id}")
    
    def extract_facts_from_text(self, text: str) -> List[LogicalFact]:
        """
        Use neural network (LLM) to extract facts from natural language
        
        Args:
            text: Natural language case description
        
        Returns:
            List of extracted facts
        """
        logger.info("🔍 Extracting facts using neural network...")
        
        # This would use LLM in real implementation
        # For now, simple keyword extraction
        facts = []
        
        # Example fact extraction (simplified)
        if "عقد" in text or "contract" in text.lower():
            facts.append(LogicalFact(
                fact_id=f"fact_{len(self.facts)}",
                statement="contract_exists",
                certainty=0.9,
                source="text_extraction"
            ))
        
        if "إيجاب" in text or "offer" in text.lower():
            facts.append(LogicalFact(
                fact_id=f"fact_{len(self.facts)+1}",
                statement="offer",
                certainty=0.85,
                source="text_extraction"
            ))
        
        if "قبول" in text or "acceptance" in text.lower():
            facts.append(LogicalFact(
                fact_id=f"fact_{len(self.facts)+2}",
                statement="acceptance",
                certainty=0.85,
                source="text_extraction"
            ))
        
        logger.info(f"Extracted {len(facts)} facts")
        return facts
    
    def forward_chaining(
        self,
        initial_facts: List[LogicalFact],
        max_iterations: int = 10
    ) -> List[LogicalFact]:
        """
        Forward chaining inference
        Start from facts, apply rules, derive conclusions
        
        Args:
            initial_facts: Starting facts
            max_iterations: Maximum inference iterations
        
        Returns:
            All derived facts
        """
        logger.info("➡️ Forward chaining inference...")
        
        # Add initial facts
        for fact in initial_facts:
            self.add_fact(fact)
        
        derived_facts = []
        
        for iteration in range(max_iterations):
            new_facts_found = False
            
            # Try each rule
            for rule_id, rule in self.rules.items():
                # Check if rule conditions are met
                if self._check_conditions(rule.condition):
                    # Check if conclusion is not already known
                    if not self._fact_exists(rule.conclusion):
                        # Derive new fact
                        new_fact = LogicalFact(
                            fact_id=f"derived_{len(self.facts)}",
                            statement=rule.conclusion,
                            certainty=rule.confidence,
                            source=f"rule_{rule_id}"
                        )
                        
                        self.add_fact(new_fact)
                        derived_facts.append(new_fact)
                        new_facts_found = True
                        
                        # Log inference
                        self.inference_history.append({
                            "iteration": iteration,
                            "rule": rule_id,
                            "derived": new_fact.statement
                        })
                        
                        logger.info(f"   Derived: {new_fact.statement} (from rule {rule_id})")
            
            # If no new facts, we're done
            if not new_facts_found:
                logger.info(f"Inference complete in {iteration+1} iterations")
                break
        
        return derived_facts
    
    def backward_chaining(
        self,
        goal: str,
        max_depth: int = 5
    ) -> Tuple[bool, List[str]]:
        """
        Backward chaining inference
        Start from goal, work backwards to find proof
        
        Args:
            goal: Goal to prove
            max_depth: Maximum search depth
        
        Returns:
            (is_provable, proof_chain)
        """
        logger.info(f"⬅️ Backward chaining for goal: {goal}")
        
        proof_chain = []
        
        # Check if goal is already a known fact
        if self._fact_exists(goal):
            return True, ["Goal is a known fact"]
        
        # Find rules that conclude the goal
        relevant_rules = [
            rule for rule in self.rules.values()
            if rule.conclusion == goal
        ]
        
        if not relevant_rules:
            return False, ["No rules found that conclude the goal"]
        
        # Try each rule
        for rule in relevant_rules:
            # Check if conditions can be proven
            conditions_met, sub_proofs = self._prove_conditions(
                rule.condition,
                depth=0,
                max_depth=max_depth
            )
            
            if conditions_met:
                proof_chain = [
                    f"Goal '{goal}' proven using rule {rule.rule_id}",
                    *sub_proofs
                ]
                return True, proof_chain
        
        return False, ["Goal cannot be proven with available rules"]
    
    def reason_about_case(
        self,
        case_text: str,
        query: str
    ) -> Dict[str, Any]:
        """
        Complete neural-symbolic reasoning about a case
        
        Process:
        1. Neural: Extract facts from natural language
        2. Symbolic: Apply logical inference
        3. Neural: Generate natural language explanation
        
        Args:
            case_text: Case description
            query: Legal question
        
        Returns:
            Reasoning result with explanation
        """
        logger.info("=" * 60)
        logger.info("🧮 Neural-Symbolic Reasoning")
        logger.info("=" * 60)
        
        # Step 1: Neural - Extract facts
        extracted_facts = self.extract_facts_from_text(case_text)
        
        # Step 2: Symbolic - Forward chaining
        derived_facts = self.forward_chaining(extracted_facts)
        
        # Step 3: Check query against derived facts
        query_conclusion = self._analyze_query(query)
        
        # Step 4: Backward chaining to prove/disprove
        is_provable, proof_chain = self.backward_chaining(query_conclusion)
        
        # Step 5: Calculate confidence
        confidence = self._calculate_confidence(extracted_facts, derived_facts)
        
        # Step 6: Generate explanation (would use LLM)
        explanation = self._generate_explanation(
            extracted_facts,
            derived_facts,
            proof_chain,
            query
        )
        
        result = {
            "query": query,
            "conclusion": "provable" if is_provable else "not_provable",
            "confidence": confidence,
            "extracted_facts": [f.to_dict() for f in extracted_facts],
            "derived_facts": [f.to_dict() for f in derived_facts],
            "proof_chain": proof_chain,
            "explanation": explanation,
            "inference_steps": len(self.inference_history)
        }
        
        logger.info(f"✅ Reasoning complete - Conclusion: {result['conclusion']}")
        logger.info("=" * 60)
        
        return result
    
    # ===== Helper Methods =====
    
    def _check_conditions(self, condition: str) -> bool:
        """Check if logical conditions are met"""
        # Simplified - would parse full logical expressions
        
        # Handle AND conjunctions
        if "∧" in condition:
            parts = condition.strip("()").split("∧")
            return all(self._fact_exists(p.strip()) for p in parts)
        
        # Handle OR disjunctions
        if "∨" in condition:
            parts = condition.strip("()").split("∨")
            return any(self._fact_exists(p.strip()) for p in parts)
        
        # Single condition
        return self._fact_exists(condition)
    
    def _fact_exists(self, statement: str) -> bool:
        """Check if a fact exists in knowledge base"""
        return any(
            fact.statement == statement
            for fact in self.facts.values()
        )
    
    def _prove_conditions(
        self,
        condition: str,
        depth: int,
        max_depth: int
    ) -> Tuple[bool, List[str]]:
        """Recursively prove conditions"""
        if depth >= max_depth:
            return False, ["Max depth reached"]
        
        # Check if already proven
        if self._check_conditions(condition):
            return True, [f"Condition '{condition}' is met"]
        
        # Try to prove sub-conditions
        # (Simplified implementation)
        return False, [f"Cannot prove condition '{condition}'"]
    
    def _analyze_query(self, query: str) -> str:
        """Convert query to goal statement"""
        # Simplified - would use NLP
        if "صحة" in query or "valid" in query.lower():
            return "valid_contract"
        elif "إثبات" in query or "proof" in query.lower():
            return "must_prove"
        else:
            return "unknown_query"
    
    def _calculate_confidence(
        self,
        extracted: List[LogicalFact],
        derived: List[LogicalFact]
    ) -> float:
        """Calculate overall confidence"""
        if not extracted and not derived:
            return 0.0
        
        all_facts = extracted + derived
        avg_certainty = sum(f.certainty for f in all_facts) / len(all_facts)
        
        return avg_certainty
    
    def _generate_explanation(
        self,
        extracted: List[LogicalFact],
        derived: List[LogicalFact],
        proof: List[str],
        query: str
    ) -> str:
        """Generate natural language explanation"""
        explanation = f"بناءً على تحليل القضية:\n\n"
        
        if extracted:
            explanation += f"الوقائع المستخرجة ({len(extracted)}):\n"
            for fact in extracted[:3]:
                explanation += f"- {fact.statement} (ثقة: {fact.certainty:.0%})\n"
        
        if derived:
            explanation += f"\nالاستنتاجات المشتقة ({len(derived)}):\n"
            for fact in derived[:3]:
                explanation += f"- {fact.statement} (من: {fact.source})\n"
        
        if proof:
            explanation += f"\nسلسلة الإثبات:\n"
            for step in proof[:3]:
                explanation += f"- {step}\n"
        
        return explanation


__all__ = [
    "NeuralSymbolicReasoning",
    "LegalRule",
    "LogicalFact",
    "RuleType",
    "LogicOperator"
]
