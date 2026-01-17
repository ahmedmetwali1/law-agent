"""
Advanced Reasoning Package
Includes all reasoning systems
"""

from .hybrid_reasoning import (
    HybridReasoningEngine,
    ReasoningMode,
    QueryComplexity,
    ReasoningStep,
    ReasoningResult
)

from .neural_symbolic import (
    NeuralSymbolicReasoning,
    LegalRule,
    LogicalFact,
    RuleType,
    LogicOperator
)

from .deontic_logic import (
    DeonticLogicSystem,
    DeonticRule,
    DeonticModality,
    DeonticOperator
)

from .temporal_logic import (
    TemporalLogicSystem,
    TemporalConstraint,
    LegalDeadline,
    TemporalOperator,
    TimeUnit
)

from .intelligent_prompts import (
    LegalDomain,
    QuestionComplexity,
    AnalyzedQuestion,
    IntelligentQueryGenerator,
    PromptBuilder,
    MAGIC_WORDS,
    LEGAL_DOMAIN_KEYWORDS,
    PROMPT_TEMPLATES
)

__all__ = [
    # Hybrid Reasoning
    "HybridReasoningEngine",
    "ReasoningMode",
    "QueryComplexity",
    "ReasoningStep",
    "ReasoningResult",
    
    # Neural-Symbolic
    "NeuralSymbolicReasoning",
    "LegalRule",
    "LogicalFact",
    "RuleType",
    "LogicOperator",
    
    # Deontic Logic
    "DeonticLogicSystem",
    "DeonticRule",
    "DeonticModality",
    "DeonticOperator",
    
    # Temporal Logic
    "TemporalLogicSystem",
    "TemporalConstraint",
    "LegalDeadline",
    "TemporalOperator",
    "TimeUnit",
    
    # Intelligent Prompts
    "LegalDomain",
    "QuestionComplexity",
    "AnalyzedQuestion",
    "IntelligentQueryGenerator",
    "PromptBuilder",
    "MAGIC_WORDS",
    "LEGAL_DOMAIN_KEYWORDS",
    "PROMPT_TEMPLATES"
]
