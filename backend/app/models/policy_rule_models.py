"""
Phase 1: Structured Rules Layer - Data Models for Policy Rules
Deterministic QA System Redesign
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class BooleanRule:
    """Boolean rule that must be true or false"""
    id: str
    description: Optional[str] = None
    value: bool = True


@dataclass
class NumericRule:
    """Numeric rule with comparison operators"""
    id: str
    value: float
    comparator: str = "le"  # le, lt, eq, ge, gt
    description: Optional[str] = None


@dataclass
class ListRule:
    """List rule that validates against a list of allowed values"""
    id: str
    items: List[str]
    description: Optional[str] = None


@dataclass
class PolicyRules:
    """Container for all policy rules organized by category"""
    rules: Dict[str, List[Any]]  # category -> list of rule objects


# Rule type constants
RULE_TYPE_BOOLEAN = "boolean"
RULE_TYPE_NUMERIC = "numeric"
RULE_TYPE_LIST = "list"

# Supported comparators for numeric rules
SUPPORTED_COMPARATORS = ["le", "lt", "eq", "ge", "gt"]
