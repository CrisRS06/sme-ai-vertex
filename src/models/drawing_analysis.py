"""
Models for drawing analysis - used as response_schema for Gemini VLM.
These schemas define the structured JSON output from the AI model.
"""
from pydantic import BaseModel, Field
from typing import List, Optional
from enum import Enum


class UnitType(str, Enum):
    """Measurement units."""
    MM = "mm"
    INCH = "in"
    CM = "cm"


class BoundingBox(BaseModel):
    """Bounding box coordinates [x1, y1, x2, y2]."""
    coordinates: List[float] = Field(..., min_length=4, max_length=4)
    page_number: Optional[int] = None


class Dimension(BaseModel):
    """A dimension extracted from the drawing."""
    feature: str = Field(..., description="Description of what is being measured (e.g., 'wall thickness', 'overall length')")
    value: float = Field(..., description="Numerical value of the dimension")
    unit: UnitType = Field(..., description="Unit of measurement")
    tolerance: Optional[str] = Field(None, description="Tolerance specification (e.g., '±0.05', '+0.1/-0.0')")
    bbox: Optional[BoundingBox] = Field(None, description="Location of dimension on drawing")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0-1")


class GDnT(BaseModel):
    """Geometric Dimensioning and Tolerancing specification."""
    symbol: str = Field(..., description="GD&T symbol (e.g., '⌖', '⏊', '∥')")
    value: str = Field(..., description="Tolerance value")
    datum_reference: Optional[str] = Field(None, description="Datum reference (e.g., 'A', 'B|C')")
    frame_bbox: Optional[BoundingBox] = Field(None, description="Location of feature control frame")
    feature_description: Optional[str] = Field(None, description="What feature this applies to")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)


class SurfaceFinish(BaseModel):
    """Surface finish specification."""
    value: str = Field(..., description="Surface finish value (e.g., 'Ra 1.6', '32 RMS')")
    location: Optional[str] = Field(None, description="Where this finish applies")
    bbox: Optional[BoundingBox] = None


class DraftAngle(BaseModel):
    """Draft angle measurement for a surface."""
    surface_description: str = Field(..., description="Description of the surface (e.g., 'outer wall', 'boss side face')")
    angle_degrees: Optional[float] = Field(None, description="Draft angle in degrees")
    angle_specification: Optional[str] = Field(None, description="Draft angle callout from drawing if present")
    is_adequate: Optional[bool] = Field(None, description="Whether draft angle meets minimum requirements")
    direction: Optional[str] = Field(None, description="Direction of draft (e.g., 'vertical', 'horizontal')")
    bbox: Optional[BoundingBox] = None


class Undercut(BaseModel):
    """Undercut feature that may require special tooling."""
    location: str = Field(..., description="Location/description of undercut feature")
    geometry_type: Optional[str] = Field(None, description="Type of undercut (e.g., 'internal thread', 'hole perpendicular to draw', 'snap fit')")
    requires_action: str = Field(..., description="Required tooling action (e.g., 'side action', 'lifter', 'hand load', 'unscrewing device')")
    complexity: Optional[str] = Field(None, description="Complexity level (simple/moderate/complex)")
    bbox: Optional[BoundingBox] = None


class WallThicknessAnalysis(BaseModel):
    """Overall wall thickness analysis."""
    minimum_mm: Optional[float] = Field(None, description="Minimum wall thickness in mm")
    maximum_mm: Optional[float] = Field(None, description="Maximum wall thickness in mm")
    nominal_mm: Optional[float] = Field(None, description="Nominal/average wall thickness in mm")
    is_uniform: Optional[bool] = Field(None, description="Whether wall thickness is reasonably uniform")
    variation_ratio: Optional[float] = Field(None, description="Max/min thickness ratio (should be <2:1 ideally)")
    thin_sections: List[str] = Field(default_factory=list, description="Descriptions of problematically thin sections")
    thick_sections: List[str] = Field(default_factory=list, description="Descriptions of problematically thick sections")


class PartingLineSuggestion(BaseModel):
    """Suggested parting line location."""
    description: str = Field(..., description="Description of suggested parting line location")
    orientation: Optional[str] = Field(None, description="Parting line orientation (e.g., 'horizontal at mid-height', 'vertical')")
    complexity: Optional[str] = Field(None, description="Parting line complexity (straight/stepped/complex)")
    reasoning: Optional[str] = Field(None, description="Why this parting line makes sense")


class GatingPoint(BaseModel):
    """Suggested gate location or gating system."""
    location: str = Field(..., description="Gate location description")
    gate_type: Optional[str] = Field(None, description="Type of gate (e.g., 'edge gate', 'sub gate', 'hot runner')")
    reasoning: Optional[str] = Field(None, description="Why this gate location is recommended")
    runner_system: Optional[str] = Field(None, description="Runner system description if shown in drawing")


class EjectionSystem(BaseModel):
    """Ejection system details."""
    ejector_pin_locations: List[str] = Field(default_factory=list, description="Locations of ejector pins if shown")
    ejection_method: Optional[str] = Field(None, description="Ejection method (e.g., 'ejector pins', 'stripper plate', 'air ejection')")
    notes: Optional[str] = Field(None, description="Any ejection-related notes from drawing")


class DrawingAnalysis(BaseModel):
    """
    Complete analysis of a technical drawing.
    This is the response_schema used with Gemini 2.5.
    """
    part_id: Optional[str] = Field(None, description="Part number or ID from drawing")
    part_name: Optional[str] = Field(None, description="Part name or description")
    material: Optional[str] = Field(None, description="Material specification (e.g., 'ABS', 'PP+30GF', 'PC/ABS')")
    material_grade: Optional[str] = Field(None, description="Specific grade if specified")

    # Core dimensional data
    dimensions: List[Dimension] = Field(
        default_factory=list,
        description="All dimensions extracted from the drawing"
    )

    # GD&T specifications
    gdandt: List[GDnT] = Field(
        default_factory=list,
        description="All GD&T specifications"
    )

    # Surface finish
    surface_finishes: List[SurfaceFinish] = Field(
        default_factory=list,
        description="Surface finish requirements"
    )

    # NEW: Injection molding-specific analysis
    draft_angles: List[DraftAngle] = Field(
        default_factory=list,
        description="Draft angle measurements for moldability"
    )

    undercuts: List[Undercut] = Field(
        default_factory=list,
        description="Undercut features requiring special tooling"
    )

    wall_thickness: Optional[WallThicknessAnalysis] = Field(
        None,
        description="Overall wall thickness analysis"
    )

    parting_line_suggestions: List[PartingLineSuggestion] = Field(
        default_factory=list,
        description="Suggested parting line locations"
    )

    gating_points: List[GatingPoint] = Field(
        default_factory=list,
        description="Suggested gate locations or gating system if shown"
    )

    ejection_system: Optional[EjectionSystem] = Field(
        None,
        description="Ejection system details if shown in drawing"
    )

    # General notes and specifications
    notes: List[str] = Field(
        default_factory=list,
        description="General notes, manufacturing instructions, or specifications from drawing"
    )

    # CAD metadata
    scale: Optional[str] = Field(None, description="Drawing scale")
    units_default: Optional[UnitType] = Field(None, description="Default units for the drawing")
    projection_type: Optional[str] = Field(None, description="Projection type (e.g., 'Third Angle', 'First Angle')")

    # Analysis metadata
    page_count: Optional[int] = Field(None, description="Number of pages analyzed")
    analysis_notes: Optional[str] = Field(None, description="Any notes about the analysis itself")


# Response schema in JSON format for Gemini API
DRAWING_ANALYSIS_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "part_id": {"type": "string"},
        "part_name": {"type": "string"},
        "material": {"type": "string"},
        "material_grade": {"type": "string"},
        "dimensions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "feature": {"type": "string"},
                    "value": {"type": "number"},
                    "unit": {"type": "string", "enum": ["mm", "in", "cm"]},
                    "tolerance": {"type": "string"},
                    "bbox": {
                        "type": "object",
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 4,
                                "maxItems": 4
                            },
                            "page_number": {"type": "integer"}
                        }
                    },
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["feature", "value", "unit"]
            }
        },
        "gdandt": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "value": {"type": "string"},
                    "datum_reference": {"type": "string"},
                    "frame_bbox": {
                        "type": "object",
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 4,
                                "maxItems": 4
                            },
                            "page_number": {"type": "integer"}
                        }
                    },
                    "feature_description": {"type": "string"},
                    "confidence": {"type": "number", "minimum": 0, "maximum": 1}
                },
                "required": ["symbol", "value"]
            }
        },
        "surface_finishes": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "value": {"type": "string"},
                    "location": {"type": "string"},
                    "bbox": {
                        "type": "object",
                        "properties": {
                            "coordinates": {
                                "type": "array",
                                "items": {"type": "number"},
                                "minItems": 4,
                                "maxItems": 4
                            },
                            "page_number": {"type": "integer"}
                        }
                    }
                },
                "required": ["value"]
            }
        },
        "draft_angles": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "surface_description": {"type": "string"},
                    "angle_degrees": {"type": "number"},
                    "angle_specification": {"type": "string"},
                    "is_adequate": {"type": "boolean"},
                    "direction": {"type": "string"},
                    "bbox": {
                        "type": "object",
                        "properties": {
                            "coordinates": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
                            "page_number": {"type": "integer"}
                        }
                    }
                },
                "required": ["surface_description"]
            }
        },
        "undercuts": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "geometry_type": {"type": "string"},
                    "requires_action": {"type": "string"},
                    "complexity": {"type": "string"},
                    "bbox": {
                        "type": "object",
                        "properties": {
                            "coordinates": {"type": "array", "items": {"type": "number"}, "minItems": 4, "maxItems": 4},
                            "page_number": {"type": "integer"}
                        }
                    }
                },
                "required": ["location", "requires_action"]
            }
        },
        "wall_thickness": {
            "type": "object",
            "properties": {
                "minimum_mm": {"type": "number"},
                "maximum_mm": {"type": "number"},
                "nominal_mm": {"type": "number"},
                "is_uniform": {"type": "boolean"},
                "variation_ratio": {"type": "number"},
                "thin_sections": {"type": "array", "items": {"type": "string"}},
                "thick_sections": {"type": "array", "items": {"type": "string"}}
            }
        },
        "parting_line_suggestions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "description": {"type": "string"},
                    "orientation": {"type": "string"},
                    "complexity": {"type": "string"},
                    "reasoning": {"type": "string"}
                },
                "required": ["description"]
            }
        },
        "gating_points": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "location": {"type": "string"},
                    "gate_type": {"type": "string"},
                    "reasoning": {"type": "string"},
                    "runner_system": {"type": "string"}
                },
                "required": ["location"]
            }
        },
        "ejection_system": {
            "type": "object",
            "properties": {
                "ejector_pin_locations": {"type": "array", "items": {"type": "string"}},
                "ejection_method": {"type": "string"},
                "notes": {"type": "string"}
            }
        },
        "notes": {
            "type": "array",
            "items": {"type": "string"}
        },
        "scale": {"type": "string"},
        "units_default": {"type": "string", "enum": ["mm", "in", "cm"]},
        "projection_type": {"type": "string"},
        "page_count": {"type": "integer"},
        "analysis_notes": {"type": "string"}
    },
    "required": ["dimensions"]
}
