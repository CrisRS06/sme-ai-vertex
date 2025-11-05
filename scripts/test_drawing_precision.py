#!/usr/bin/env python3
"""
Test Drawing Analysis Precision

Tests the two-step reading process:
1. Gemini VLM (visual understanding)
2. Document AI OCR (precision fallback)

Usage:
    python scripts/test_drawing_precision.py path/to/drawing.pdf

Outputs:
    - JSON with all extracted fields
    - Confidence scores for each dimension
    - Comparison of VLM vs OCR results
    - Precision metrics
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.services.drawing_analyzer import DrawingAnalyzer
from src.services.exception_engine import ExceptionEngine
from src.config.settings import settings


async def test_drawing_analysis(pdf_path: str) -> Dict[str, Any]:
    """
    Test drawing analysis with detailed output.

    Args:
        pdf_path: Path to PDF drawing

    Returns:
        Analysis results with metrics
    """
    print("=" * 80)
    print("🔬 TECHNICAL DRAWING PRECISION TEST")
    print("=" * 80)
    print()

    # Validate file exists
    if not Path(pdf_path).exists():
        raise FileNotFoundError(f"Drawing not found: {pdf_path}")

    print(f"📄 Drawing: {pdf_path}")
    print(f"📊 Quality Mode: {settings.quality_mode}")
    print(f"🔧 OCR Fallback: {settings.enable_document_ai_fallback}")
    print(f"📉 OCR Threshold: {settings.ocr_confidence_threshold}")
    print()

    # Initialize analyzer
    print("🚀 Initializing Gemini VLM...")
    analyzer = DrawingAnalyzer(enable_context_caching=True)

    # Read PDF
    print("📖 Reading PDF file...")
    with open(pdf_path, 'rb') as f:
        pdf_content = f.read()

    print(f"   Size: {len(pdf_content):,} bytes")
    print()

    # Analyze with VLM + OCR fallback
    print("=" * 80)
    print("STEP 1: GEMINI VLM VISUAL ANALYSIS")
    print("=" * 80)
    print()

    analysis_id = f"test_{Path(pdf_path).stem}"

    try:
        analysis = await analyzer.analyze_drawing_from_pdf(
            pdf_content=pdf_content,
            analysis_id=analysis_id
        )

        print("✅ Analysis completed successfully!")
        print()

        # Display results
        print("=" * 80)
        print("EXTRACTION RESULTS")
        print("=" * 80)
        print()

        # Part Info
        print("📋 Part Information:")
        print(f"   Part ID:       {analysis.part_id or 'N/A'}")
        print(f"   Part Name:     {analysis.part_name or 'N/A'}")
        print(f"   Material:      {analysis.material or 'Not specified'}")
        print(f"   Material Grade: {analysis.material_grade or 'N/A'}")
        print()

        # Dimensions
        print(f"📏 Dimensions Extracted: {len(analysis.dimensions)}")
        if analysis.dimensions:
            print()
            print("   Top 10 dimensions:")
            for i, dim in enumerate(analysis.dimensions[:10], 1):
                conf_str = f"conf={dim.confidence:.2f}" if dim.confidence else "conf=N/A"
                tol_str = f"±{dim.tolerance}" if dim.tolerance else "no tolerance"
                print(f"   {i:2}. {dim.feature:30s} = {dim.value:8} {dim.unit:3s}  ({tol_str}, {conf_str})")

            if len(analysis.dimensions) > 10:
                print(f"   ... and {len(analysis.dimensions) - 10} more")
        print()

        # Confidence Analysis
        dims_with_conf = [d for d in analysis.dimensions if d.confidence is not None]
        if dims_with_conf:
            avg_conf = sum(d.confidence for d in dims_with_conf) / len(dims_with_conf)
            low_conf = [d for d in dims_with_conf if d.confidence < 0.7]

            print(f"📊 Confidence Metrics:")
            print(f"   Average:     {avg_conf:.3f}")
            print(f"   Low (<0.7):  {len(low_conf)} dimensions")
            print(f"   High (≥0.7): {len(dims_with_conf) - len(low_conf)} dimensions")

            if low_conf:
                print()
                print("   ⚠️  Low confidence dimensions (OCR fallback triggered):")
                for dim in low_conf[:5]:
                    print(f"      - {dim.feature}: {dim.value} {dim.unit} (conf={dim.confidence:.2f})")
        print()

        # GD&T
        print(f"🎯 GD&T Specifications: {len(analysis.gdandt)}")
        if analysis.gdandt:
            for i, gd in enumerate(analysis.gdandt[:5], 1):
                print(f"   {i}. {gd.symbol} {gd.value} {gd.datum_reference or ''} → {gd.feature_description or 'N/A'}")
        print()

        # Surface Finishes
        print(f"✨ Surface Finishes: {len(analysis.surface_finishes)}")
        if analysis.surface_finishes:
            for i, sf in enumerate(analysis.surface_finishes[:3], 1):
                print(f"   {i}. {sf.value} on {sf.location or 'unspecified location'}")
        print()

        # NEW: Injection Molding Analysis
        print("🏭 INJECTION MOLDING ANALYSIS:")
        print()

        # Draft Angles
        print(f"   📐 Draft Angles: {len(analysis.draft_angles)}")
        if analysis.draft_angles:
            for da in analysis.draft_angles[:3]:
                angle = f"{da.angle_degrees}°" if da.angle_degrees else da.angle_specification or "N/A"
                adequate = "✅ adequate" if da.is_adequate else "⚠️ insufficient"
                print(f"      - {da.surface_description}: {angle} ({adequate})")
        print()

        # Undercuts
        print(f"   🔧 Undercuts: {len(analysis.undercuts)}")
        if analysis.undercuts:
            for uc in analysis.undercuts:
                print(f"      - {uc.location}: requires {uc.requires_action} ({uc.complexity or 'complexity N/A'})")
        print()

        # Wall Thickness
        if analysis.wall_thickness:
            wt = analysis.wall_thickness
            print(f"   📊 Wall Thickness Analysis:")
            print(f"      Min: {wt.minimum_mm}mm, Max: {wt.maximum_mm}mm, Nominal: {wt.nominal_mm}mm")
            print(f"      Uniform: {wt.is_uniform}, Variation ratio: {wt.variation_ratio or 'N/A'}")
            if wt.thin_sections:
                print(f"      ⚠️  Thin sections: {', '.join(wt.thin_sections[:2])}")
        else:
            print(f"   📊 Wall Thickness: Not analyzed")
        print()

        # Parting Lines
        print(f"   🔀 Parting Line Suggestions: {len(analysis.parting_line_suggestions)}")
        if analysis.parting_line_suggestions:
            for pl in analysis.parting_line_suggestions:
                print(f"      - {pl.description} ({pl.complexity or 'complexity N/A'})")
        print()

        # Gating
        print(f"   🚪 Gating Points: {len(analysis.gating_points)}")
        if analysis.gating_points:
            for gp in analysis.gating_points:
                print(f"      - {gp.location}: {gp.gate_type or 'type N/A'}")
        print()

        # Notes
        print(f"📝 General Notes: {len(analysis.notes)}")
        if analysis.notes:
            for i, note in enumerate(analysis.notes[:3], 1):
                print(f"   {i}. {note[:80]}{'...' if len(note) > 80 else ''}")
        print()

        # Validation
        validation = analyzer.validate_analysis(analysis)
        print("=" * 80)
        print("VALIDATION REPORT")
        print("=" * 80)
        print()
        print(f"✅ Valid: {validation['valid']}")

        if validation['issues']:
            print(f"❌ Issues ({len(validation['issues'])}):")
            for issue in validation['issues']:
                print(f"   - {issue}")

        if validation['warnings']:
            print(f"⚠️  Warnings ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                print(f"   - {warning}")
        print()

        # Save JSON output
        output_path = Path(pdf_path).parent / f"{Path(pdf_path).stem}_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(analysis.model_dump(mode='json'), f, indent=2, default=str)

        print(f"💾 Full analysis saved to: {output_path}")
        print()

        # Run Exception Engine
        print("=" * 80)
        print("EXCEPTION ANALYSIS")
        print("=" * 80)
        print()

        print("🔍 Running Exception Engine...")
        engine = ExceptionEngine()
        exception_report = engine.validate_analysis(analysis, analysis_id)

        print()
        print(f"📊 Exceptions Found: {exception_report.summary.total_exceptions}")
        print(f"   🔴 Critical: {exception_report.summary.critical_count}")
        print(f"   🟡 Warnings: {exception_report.summary.warning_count}")
        print(f"   🔵 Info:     {exception_report.summary.info_count}")
        print()
        print(f"✅ Can Proceed: {exception_report.summary.can_proceed}")
        print(f"⚠️  Risk Level: {exception_report.summary.overall_risk_level.upper()}")
        print()

        if exception_report.exceptions:
            print("Top 5 Exceptions:")
            for i, exc in enumerate(exception_report.exceptions[:5], 1):
                severity_icon = {"critical": "🔴", "warning": "🟡", "info": "🔵"}[exc.severity.value]
                print(f"{i}. {severity_icon} [{exc.category.value}] {exc.title}")
                print(f"   → {exc.recommended_change[:100]}...")

        print()
        print("=" * 80)
        print("✅ TEST COMPLETE")
        print("=" * 80)

        return {
            "analysis": analysis,
            "exceptions": exception_report,
            "validation": validation,
            "metrics": {
                "dimensions_count": len(analysis.dimensions),
                "average_confidence": avg_conf if dims_with_conf else None,
                "low_confidence_count": len(low_conf) if dims_with_conf else 0,
                "exceptions_count": exception_report.summary.total_exceptions,
                "critical_exceptions": exception_report.summary.critical_count
            }
        }

    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        import traceback
        traceback.print_exc()
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_drawing_precision.py path/to/drawing.pdf")
        print()
        print("Example:")
        print("  python scripts/test_drawing_precision.py samples/part_123.pdf")
        sys.exit(1)

    pdf_path = sys.argv[1]

    # Run test
    asyncio.run(test_drawing_analysis(pdf_path))


if __name__ == "__main__":
    main()
