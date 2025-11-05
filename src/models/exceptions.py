"""
Models for molding exceptions and feasibility issues.
These represent the "exception report" findings.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum


class ExceptionSeverity(str, Enum):
    """Severity level of an exception."""
    CRITICAL = "critical"  # Cannot proceed without change
    WARNING = "warning"    # Can proceed with risk
    INFO = "info"          # Best practice recommendation


class ExceptionCategory(str, Enum):
    """Category of molding exception."""
    DIMENSION = "dimension"                    # Dimensional tolerance issues
    WALL_THICKNESS = "wall_thickness"          # Wall thickness problems
    DRAFT_ANGLE = "draft_angle"                # Insufficient draft
    UNDERCUT = "undercut"                      # Undercuts detected
    MATERIAL = "material"                      # Material-related issues
    SURFACE_FINISH = "surface_finish"          # Surface finish concerns
    GDANDT = "gdandt"                          # GD&T specification issues
    MOLDING_DEFECT_RISK = "molding_defect_risk"  # Flash, short shot, knit line, etc.
    PARTING_LINE = "parting_line"              # Parting line location and complexity
    GATING = "gating"                          # Gate location and runner system
    SHRINKAGE_WARPAGE = "shrinkage_warpage"    # Material shrinkage and warpage prediction
    PRESS_CAPABILITY = "press_capability"      # Press tonnage and capability validation
    ASSEMBLY = "assembly"                      # Assembly-related issues
    OTHER = "other"


class DefectType(str, Enum):
    """Types of molding defects."""
    FLASH = "flash"
    SHORT_SHOT = "short_shot"
    SINK_MARK = "sink_mark"
    WARP = "warp"
    KNIT_LINE = "knit_line"
    BURN_MARK = "burn_mark"
    FLOW_LINES = "flow_lines"
    EJECTION_ISSUE = "ejection_issue"          # Part sticking or ejection problems


class MoldingException(BaseModel):
    """A single exception found in the drawing analysis."""
    exception_id: str = Field(..., description="Unique identifier for this exception")
    severity: ExceptionSeverity
    category: ExceptionCategory

    # Issue description
    title: str = Field(..., description="Short title of the issue")
    description: str = Field(..., description="Detailed description of the problem")

    # What was found
    current_specification: Optional[str] = Field(None, description="What the drawing currently specifies")
    recommended_change: Optional[str] = Field(None, description="Recommended change or action")

    # Reasoning
    reasoning: str = Field(..., description="Why this is an issue (based on best practices)")
    reference: Optional[str] = Field(None, description="Reference to standard or best practice")

    # Location in drawing
    page_number: Optional[int] = None
    bbox: Optional[List[float]] = Field(None, description="Bounding box [x1, y1, x2, y2]")
    dimension_reference: Optional[str] = Field(None, description="Reference to specific dimension or feature")

    # Risk assessment
    defect_risk: Optional[DefectType] = Field(None, description="Specific defect risk if applicable")
    probability_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Probability of issue occurring (0-1)")

    # Additional context
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExceptionSummary(BaseModel):
    """Summary of all exceptions found."""
    total_exceptions: int
    critical_count: int
    warning_count: int
    info_count: int
    exceptions_by_category: Dict[str, int]
    can_proceed: bool = Field(..., description="Whether fabrication can proceed with current spec")
    overall_risk_level: str = Field(..., description="Overall risk: low, medium, high")


class ExceptionReport(BaseModel):
    """Complete exception report for a drawing."""
    analysis_id: str
    part_id: Optional[str] = None
    part_name: Optional[str] = None

    # Summary
    summary: ExceptionSummary

    # All exceptions
    exceptions: List[MoldingException]

    # Recommendations
    executive_summary: str = Field(..., description="Executive summary for client")
    action_items: List[str] = Field(default_factory=list, description="List of actions needed before proceeding")

    # Sign-off required
    requires_client_approval: bool = True
    approval_notes: Optional[str] = Field(None, description="Notes about what needs client sign-off")


class BestPracticeRule(BaseModel):
    """A best practice rule for injection molding."""
    rule_id: str
    category: ExceptionCategory
    description: str
    threshold: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Threshold values")
    applies_to_materials: Optional[List[str]] = Field(None, description="Specific materials this applies to")
    reference: Optional[str] = Field(None, description="Reference to standard or manual")
