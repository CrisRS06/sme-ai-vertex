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
