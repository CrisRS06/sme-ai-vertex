"""
Exception Engine Service
Validates drawing analysis against injection molding best practices.
Generates exception reports highlighting manufacturability issues.
"""
import uuid
from typing import List, Dict, Any, Optional
import structlog

from src.models.drawing_analysis import DrawingAnalysis, Dimension, GDnT
from src.models.exceptions import (
    MoldingException,
    ExceptionReport,
    ExceptionSummary,
    ExceptionSeverity,
    ExceptionCategory,
    DefectType,
    BestPracticeRule
)

logger = structlog.get_logger()


class ExceptionEngine:
    """
    Engine for validating drawings against injection molding best practices.

    Based on Michael's requirements from meetings:
    - Detect dimensional issues that can't be manufactured
    - Identify GD&T specs that exceed capabilities
    - Flag molding defect risks (flash, warp, short shot, knit lines)
    - Categorize by severity (critical = can't proceed, warning = risky, info = best practice)
    """

    def __init__(self):
        self.rules = self._initialize_rules()
        logger.info("exception_engine_initialized", rules_count=len(self.rules))

    def _initialize_rules(self) -> List[BestPracticeRule]:
        """
        Initialize best practice rules for injection molding.

        Based on:
        - Michael's meeting notes (R7-R9)
        - Standard injection molding practices
        - Material-specific requirements
        """
        rules = [
            # Wall Thickness Rules
            BestPracticeRule(
                rule_id="WT001",
                category=ExceptionCategory.WALL_THICKNESS,
                description="Minimum wall thickness for thermoplastics",
                threshold={"min_mm": 0.6, "recommended_mm": 1.0},
                applies_to_materials=["ABS", "PP", "PC", "PA", "POM"],
                reference="Standard molding practice - mentioned by Michael in R9"
            ),
            BestPracticeRule(
                rule_id="WT002",
                category=ExceptionCategory.WALL_THICKNESS,
                description="Maximum wall thickness to avoid sink marks",
                threshold={"max_mm": 4.0, "recommended_mm": 3.0},
                applies_to_materials=["ABS", "PP", "PC"],
                reference="Prevents sink marks and long cycle times"
            ),
            BestPracticeRule(
                rule_id="WT003",
                category=ExceptionCategory.WALL_THICKNESS,
                description="Wall thickness variation ratio",
                threshold={"max_ratio": 3.0, "recommended_ratio": 2.0},
                applies_to_materials=None,  # Applies to all
                reference="Avoid flow imbalance and warpage"
            ),

            # Draft Angle Rules
            BestPracticeRule(
                rule_id="DA001",
                category=ExceptionCategory.DRAFT_ANGLE,
                description="Minimum draft angle for smooth surfaces",
                threshold={"min_degrees": 0.5, "recommended_degrees": 1.5},
                applies_to_materials=["ABS", "PP", "PC"],
                reference="Required for part ejection"
            ),
            BestPracticeRule(
                rule_id="DA002",
                category=ExceptionCategory.DRAFT_ANGLE,
                description="Minimum draft for textured surfaces",
                threshold={"min_degrees": 1.5, "recommended_degrees": 2.5},
                applies_to_materials=["ABS", "PP", "PC"],
                reference="Textured surfaces require more draft"
            ),

            # Tolerance Rules
            BestPracticeRule(
                rule_id="TOL001",
                category=ExceptionCategory.DIMENSION,
                description="Achievable tolerance for ABS parts",
                threshold={"min_mm": 0.05, "typical_mm": 0.1},
                applies_to_materials=["ABS"],
                reference="Standard ABS molding tolerance"
            ),
            BestPracticeRule(
                rule_id="TOL002",
                category=ExceptionCategory.DIMENSION,
                description="Achievable tolerance for PP parts",
                threshold={"min_mm": 0.08, "typical_mm": 0.15},
                applies_to_materials=["PP"],
                reference="PP has higher shrinkage variability"
            ),
        ]
        return rules

    def validate_analysis(
        self,
        analysis: DrawingAnalysis,
        analysis_id: str
    ) -> ExceptionReport:
        """
        Validate drawing analysis and generate exception report.

        Args:
            analysis: DrawingAnalysis from VLM
            analysis_id: Unique analysis identifier

        Returns:
            ExceptionReport with all found issues
        """
        try:
            logger.info(
                "validating_analysis",
                analysis_id=analysis_id,
                dimensions=len(analysis.dimensions),
                gdandt=len(analysis.gdandt)
            )

            exceptions = []

            # Run all validation checks
            exceptions.extend(self._check_wall_thickness(analysis))
            exceptions.extend(self._check_dimensions_tolerance(analysis))
            exceptions.extend(self._check_draft_angles(analysis))
            exceptions.extend(self._check_gdandt_specs(analysis))
            exceptions.extend(self._check_surface_finish(analysis))
            exceptions.extend(self._check_defect_risks(analysis))
            exceptions.extend(self._check_material_compatibility(analysis))

            # NEW: Expanded technical category checks
            exceptions.extend(self._check_undercuts(analysis))
            exceptions.extend(self._check_parting_line(analysis))
            exceptions.extend(self._check_gating(analysis))
            exceptions.extend(self._check_shrinkage_warpage(analysis))
            exceptions.extend(self._check_press_capabilities(analysis))

            # Generate summary
            summary = self._generate_summary(exceptions)

            # Generate executive summary text
            executive_summary = self._generate_executive_summary(analysis, exceptions, summary)

            # Generate action items
            action_items = self._generate_action_items(exceptions)

            report = ExceptionReport(
                analysis_id=analysis_id,
                part_id=analysis.part_id,
                part_name=analysis.part_name,
                summary=summary,
                exceptions=exceptions,
                executive_summary=executive_summary,
                action_items=action_items,
                requires_client_approval=summary.critical_count > 0
            )

            logger.info(
                "validation_completed",
                analysis_id=analysis_id,
                total_exceptions=len(exceptions),
                critical=summary.critical_count,
                warnings=summary.warning_count
            )

            return report

        except Exception as e:
            logger.error("validation_failed", error=str(e), analysis_id=analysis_id)
            raise

    def _check_wall_thickness(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check wall thickness against best practices."""
        exceptions = []

        wall_dims = [
            d for d in analysis.dimensions
            if any(keyword in d.feature.lower() for keyword in ["wall", "thickness", "rib"])
        ]

        for dim in wall_dims:
            # Convert to mm if in inches
            value_mm = dim.value if dim.unit == "mm" else dim.value * 25.4

            # Check minimum thickness (from R9 meeting - can't go below 0.6mm)
            if value_mm < 0.6:
                exceptions.append(MoldingException(
                    exception_id=str(uuid.uuid4()),
                    severity=ExceptionSeverity.CRITICAL,
                    category=ExceptionCategory.WALL_THICKNESS,
                    title=f"Wall thickness below minimum ({value_mm:.2f}mm)",
                    description=f"Feature '{dim.feature}' has wall thickness of {value_mm:.2f}mm, "
                               f"which is below the minimum manufacturable thickness of 0.6mm.",
                    current_specification=f"{dim.value} {dim.unit}",
                    recommended_change="Increase wall thickness to minimum 0.6mm (recommended 1.0mm or greater)",
                    reasoning="Wall thickness below 0.6mm is difficult to fill consistently and may result "
                             "in short shots, incomplete filling, or excessive injection pressures. "
                             "As mentioned in feasibility review, micro cannot reliably mold below 0.6mm.",
                    reference="Rule WT001 - Minimum wall thickness for thermoplastics",
                    bbox=dim.bbox.coordinates if dim.bbox else None,
                    defect_risk=DefectType.SHORT_SHOT,
                    probability_score=0.9
                ))

            # Check maximum thickness (sink marks)
            elif value_mm > 4.0:
                exceptions.append(MoldingException(
                    exception_id=str(uuid.uuid4()),
                    severity=ExceptionSeverity.WARNING,
                    category=ExceptionCategory.WALL_THICKNESS,
                    title=f"Thick wall section ({value_mm:.2f}mm) - sink risk",
                    description=f"Feature '{dim.feature}' has wall thickness of {value_mm:.2f}mm, "
                               f"which may cause sink marks and long cycle times.",
                    current_specification=f"{dim.value} {dim.unit}",
                    recommended_change="Reduce to 3-4mm maximum or add coring to reduce thickness",
                    reasoning="Thick sections cool slowly and may result in sink marks, voids, or warpage. "
                             "They also increase cycle time significantly.",
                    reference="Rule WT002 - Maximum wall thickness",
                    defect_risk=DefectType.SINK_MARK,
                    probability_score=0.7
                ))

        return exceptions

    def _check_dimensions_tolerance(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check if dimensional tolerances are achievable."""
        exceptions = []

        for dim in analysis.dimensions:
            if not dim.tolerance:
                continue  # No tolerance specified

            # Parse tolerance (simplified - handles ±X.XX format)
            try:
                tolerance_str = dim.tolerance.replace("±", "").replace(" ", "")
                tolerance_value = float(tolerance_str)

                # Convert to mm
                tolerance_mm = tolerance_value if dim.unit == "mm" else tolerance_value * 25.4

                # Check if tolerance is too tight (< 0.05mm typical limit)
                if tolerance_mm < 0.05:
                    exceptions.append(MoldingException(
                        exception_id=str(uuid.uuid4()),
                        severity=ExceptionSeverity.CRITICAL,
                        category=ExceptionCategory.DIMENSION,
                        title=f"Tolerance too tight ({tolerance_mm:.3f}mm)",
                        description=f"Dimension '{dim.feature}' specifies tolerance of ±{tolerance_mm:.3f}mm, "
                                   f"which is beyond standard molding capabilities.",
                        current_specification=f"{dim.value} {dim.tolerance} {dim.unit}",
                        recommended_change=f"Relax tolerance to ±0.05mm or tighter (typical ±0.1mm)",
                        reasoning="Injection molding typically achieves ±0.05-0.10mm tolerance. "
                                 "Tighter tolerances require secondary operations or may be impossible to maintain.",
                        reference="Rule TOL001 - Achievable tolerance limits",
                        bbox=dim.bbox.coordinates if dim.bbox else None,
                        probability_score=0.85
                    ))

            except (ValueError, AttributeError):
                # Could not parse tolerance - log warning
                logger.warning("tolerance_parse_failed", tolerance=dim.tolerance, feature=dim.feature)

        return exceptions

    def _check_draft_angles(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check for draft angle issues."""
        exceptions = []

        # Look for draft mentions in notes or dimensions
        draft_notes = [
            note for note in analysis.notes
            if "draft" in note.lower()
        ]

        # If no draft mentioned at all, flag as warning
        if not draft_notes:
            exceptions.append(MoldingException(
                exception_id=str(uuid.uuid4()),
                severity=ExceptionSeverity.WARNING,
                category=ExceptionCategory.DRAFT_ANGLE,
                title="No draft angles specified",
                description="Drawing does not specify draft angles. All vertical walls require draft for ejection.",
                current_specification="No draft specification found",
                recommended_change="Add minimum 0.5° draft on all vertical surfaces (1.5° recommended)",
                reasoning="Without draft angles, parts may stick in the mold or require excessive ejection force, "
                         "leading to damage or deformation.",
                reference="Rule DA001 - Minimum draft requirements"
            ))

        return exceptions

    def _check_gdandt_specs(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check GD&T specifications for feasibility."""
        exceptions = []

        for gdandt in analysis.gdandt:
            # Parse tolerance value (simplified)
            try:
                # Extract numeric value from tolerance string
                value_str = ''.join(c for c in gdandt.value if c.isdigit() or c == '.')
                if value_str:
                    tolerance_val = float(value_str)

                    # Check if very tight (< 0.05mm)
                    if tolerance_val < 0.05:
                        exceptions.append(MoldingException(
                            exception_id=str(uuid.uuid4()),
                            severity=ExceptionSeverity.CRITICAL,
                            category=ExceptionCategory.GDANDT,
                            title=f"GD&T tolerance too tight ({gdandt.symbol}: {gdandt.value})",
                            description=f"GD&T specification '{gdandt.symbol}' with tolerance {gdandt.value} "
                                       f"may be difficult to achieve with injection molding.",
                            current_specification=f"{gdandt.symbol} {gdandt.value} {gdandt.datum_reference or ''}",
                            recommended_change="Relax GD&T tolerance to 0.05mm or greater where possible",
                            reasoning="Tight geometric tolerances require precise mold making and may need "
                                     "secondary operations to achieve.",
                            reference="Standard GD&T molding capabilities",
                            frame_bbox=gdandt.frame_bbox.coordinates if gdandt.frame_bbox else None
                        ))

            except (ValueError, AttributeError):
                logger.warning("gdandt_parse_failed", gdandt=gdandt.value, symbol=gdandt.symbol)

        return exceptions

    def _check_surface_finish(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check surface finish requirements."""
        exceptions = []

        for finish in analysis.surface_finishes:
            # Check for very fine finishes that are expensive
            if any(indicator in finish.value.lower() for indicator in ["mirror", "polish", "0.1", "0.2"]):
                exceptions.append(MoldingException(
                    exception_id=str(uuid.uuid4()),
                    severity=ExceptionSeverity.INFO,
                    category=ExceptionCategory.SURFACE_FINISH,
                    title=f"High-quality surface finish specified ({finish.value})",
                    description=f"Surface finish '{finish.value}' requires premium mold finish and may increase cost.",
                    current_specification=finish.value,
                    recommended_change="Consider standard finish if acceptable for application",
                    reasoning="Mirror or high-polish finishes require diamond-polished molds and careful processing. "
                             "They also show defects more readily.",
                    reference="Surface finish best practices"
                ))

        return exceptions

    def _check_defect_risks(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """
        Analyze for molding defect risks.

        Based on Michael's requirements (R9):
        - Flash (tight clearances)
        - Short shot (thin walls, long flow)
        - Warp (Gen6 had 12 thousandths warp issue)
        - Knit lines (complex geometry)
        """
        exceptions = []

        # Check for warp risk (large flat areas with tight tolerances)
        large_dims = [d for d in analysis.dimensions if d.value > 100]  # >100mm or >4in
        if large_dims and analysis.material:
            exceptions.append(MoldingException(
                exception_id=str(uuid.uuid4()),
                severity=ExceptionSeverity.WARNING,
                category=ExceptionCategory.MOLDING_DEFECT_RISK,
                title="Warpage risk on large dimensions",
                description=f"Part has large dimensions ({len(large_dims)} features >100mm) which may warp during cooling. "
                           f"Material: {analysis.material}",
                current_specification=f"Large features with tight tolerances",
                recommended_change="Consider adding ribs for rigidity, or relax tolerances accounting for warp",
                reasoning="Large flat parts tend to warp during cooling due to differential shrinkage. "
                         "Gen6 case study showed 12 thousandths warp on similar geometry.",
                reference="Gen6 lesson learned - warpage on large parts",
                defect_risk=DefectType.WARP,
                probability_score=0.6
            ))

        return exceptions

    def _check_material_compatibility(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check if specifications are compatible with material."""
        exceptions = []

        if not analysis.material:
            exceptions.append(MoldingException(
                exception_id=str(uuid.uuid4()),
                severity=ExceptionSeverity.WARNING,
                category=ExceptionCategory.MATERIAL,
                title="Material not specified",
                description="Drawing does not specify material. Material selection affects feasibility.",
                current_specification="No material specification",
                recommended_change="Specify material (e.g., ABS, PP, PC/ABS, PA6+GF30)",
                reasoning="Different materials have different shrinkage rates, flow characteristics, and "
                         "tolerance capabilities. Material must be specified for accurate feasibility assessment.",
                reference="Material specification requirement"
            ))

        return exceptions

    def _check_undercuts(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check for undercut features that require special tooling."""
        exceptions = []

        # Check undercuts extracted by VLM
        for undercut in analysis.undercuts:
            severity = ExceptionSeverity.CRITICAL if "slide" in undercut.requires_action.lower() or \
                                                      "lifter" in undercut.requires_action.lower() else \
                       ExceptionSeverity.WARNING

            exceptions.append(MoldingException(
                exception_id=str(uuid.uuid4()),
                severity=severity,
                category=ExceptionCategory.UNDERCUT,
                title=f"Undercut detected: {undercut.location}",
                description=f"Feature '{undercut.location}' contains an undercut ({undercut.geometry_type or 'type not specified'}) "
                           f"that requires {undercut.requires_action} for manufacturing.",
                current_specification=f"Undercut feature: {undercut.geometry_type or 'geometry type not specified'}",
                recommended_change=f"Accept {undercut.requires_action} (increases tooling cost) or modify geometry to eliminate undercut",
                reasoning=f"Undercuts prevent straight pull from mold and require {undercut.requires_action}. "
                         f"This adds complexity and cost to the mold. Side actions typically add $5,000-$15,000 to tooling cost.",
                reference="Rule UC001 - Undercut handling",
                bbox=undercut.bbox.coordinates if undercut.bbox else None,
                defect_risk=DefectType.EJECTION_ISSUE,
                probability_score=0.8 if severity == ExceptionSeverity.CRITICAL else 0.5
            ))

        # If no undercuts detected but part has complex geometry, flag as info
        if not analysis.undercuts and len(analysis.dimensions) > 10:
            exceptions.append(MoldingException(
                exception_id=str(uuid.uuid4()),
                severity=ExceptionSeverity.INFO,
                category=ExceptionCategory.UNDERCUT,
                title="Undercut analysis completed - none detected",
                description="No undercuts detected in drawing analysis. Verify no hidden features prevent straight pull.",
                current_specification="No undercuts found",
                recommended_change="Review 3D geometry to confirm no hidden undercuts",
                reasoning="Complex parts may have undercuts not visible in 2D views.",
                reference="Best practice - undercut verification"
            ))

        return exceptions

    def _check_parting_line(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Analyze parting line suggestions."""
        exceptions = []

        if not analysis.parting_line_suggestions:
            # No parting line suggested - flag as info
            exceptions.append(MoldingException(
                exception_id=str(uuid.uuid4()),
                severity=ExceptionSeverity.INFO,
                category=ExceptionCategory.PARTING_LINE,
                title="No parting line specified",
                description="Drawing does not specify preferred parting line location. "
                           "Mold designer will determine optimal parting line.",
                current_specification="No parting line specification",
                recommended_change="Consider specifying parting line if cosmetic appearance on split line is critical",
                reasoning="Parting line location affects appearance (flash line visible), tooling complexity, "
                         "and ejection. Customer may want to specify for aesthetic parts.",
                reference="Best practice - parting line specification"
            ))
        else:
            # Analyze suggested parting lines
            for pl in analysis.parting_line_suggestions:
                if pl.complexity and pl.complexity.lower() == "complex":
                    exceptions.append(MoldingException(
                        exception_id=str(uuid.uuid4()),
                        severity=ExceptionSeverity.WARNING,
                        category=ExceptionCategory.PARTING_LINE,
                        title=f"Complex parting line: {pl.description}",
                        description=f"Suggested parting line '{pl.description}' has complex geometry. "
                                   f"Reasoning: {pl.reasoning or 'Not specified'}",
                        current_specification=f"Complex parting line - {pl.orientation or 'orientation not specified'}",
                        recommended_change="Complex parting lines increase tooling cost. Simplify geometry if possible.",
                        reasoning="Stepped or complex parting lines require more machining time and may have "
                                 "tighter fit requirements to prevent flash.",
                        reference="Rule PL001 - Parting line complexity"
                    ))

        return exceptions

    def _check_gating(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Check gating and runner system if specified."""
        exceptions = []

        if not analysis.gating_points:
            # No gating specified - this is normal for most drawings
            exceptions.append(MoldingException(
                exception_id=str(uuid.uuid4()),
                severity=ExceptionSeverity.INFO,
                category=ExceptionCategory.GATING,
                title="No gate location specified",
                description="Drawing does not specify gate location. Mold designer will determine optimal gate placement.",
                current_specification="No gating specification",
                recommended_change="Consider specifying gate location if witness marks must be avoided in critical areas",
                reasoning="Gate location affects fill pattern, weld lines, and leaves witness marks. "
                         "For cosmetic parts, customer may want to specify gate location.",
                reference="Best practice - gate location"
            ))
        else:
            # Analyze suggested gates
            for gate in analysis.gating_points:
                # Check if gate type is specified
                if gate.gate_type and "hot runner" in gate.gate_type.lower():
                    exceptions.append(MoldingException(
                        exception_id=str(uuid.uuid4()),
                        severity=ExceptionSeverity.INFO,
                        category=ExceptionCategory.GATING,
                        title=f"Hot runner system specified: {gate.location}",
                        description=f"Gate location '{gate.location}' specifies hot runner system. "
                                   f"Reasoning: {gate.reasoning or 'Not specified'}",
                        current_specification=f"Hot runner at {gate.location}",
                        recommended_change="Hot runner systems add $10,000-$30,000+ to tooling cost but eliminate "
                                          "runner waste and reduce cycle time.",
                        reasoning="Hot runners are beneficial for high-volume production but have high upfront cost.",
                        reference="Rule GT001 - Hot runner considerations"
                    ))

        return exceptions

    def _check_shrinkage_warpage(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Predict shrinkage and warpage risks based on material and geometry."""
        exceptions = []

        if not analysis.material:
            return exceptions  # Can't predict without material

        material = analysis.material.upper()

        # Material shrinkage data (typical ranges)
        shrinkage_data = {
            "PP": {"min": 1.0, "max": 2.5, "risk": "high"},
            "PP+GF": {"min": 0.3, "max": 0.8, "risk": "medium"},
            "ABS": {"min": 0.4, "max": 0.7, "risk": "low"},
            "PC": {"min": 0.5, "max": 0.7, "risk": "low"},
            "PA6": {"min": 0.8, "max": 2.0, "risk": "high"},
            "PA6+GF": {"min": 0.2, "max": 0.6, "risk": "low"},
            "POM": {"min": 1.8, "max": 2.2, "risk": "high"},
        }

        # Find matching material
        shrink_info = None
        for mat_key, data in shrinkage_data.items():
            if mat_key in material or material in mat_key:
                shrink_info = data
                break

        if shrink_info:
            if shrink_info["risk"] == "high":
                exceptions.append(MoldingException(
                    exception_id=str(uuid.uuid4()),
                    severity=ExceptionSeverity.WARNING,
                    category=ExceptionCategory.SHRINKAGE_WARPAGE,
                    title=f"High shrinkage material: {analysis.material}",
                    description=f"Material {analysis.material} has high shrinkage rate "
                               f"({shrink_info['min']}-{shrink_info['max']}%), "
                               f"which may affect dimensional accuracy and cause warpage.",
                    current_specification=f"Material: {analysis.material}",
                    recommended_change=f"Account for {shrink_info['min']}-{shrink_info['max']}% shrinkage in tooling. "
                                      f"Consider glass-filled grade to reduce shrinkage.",
                    reasoning="High-shrinkage materials are more difficult to hold tight tolerances and more prone "
                             "to warpage, especially on large flat parts. Shrinkage varies with wall thickness, "
                             "flow direction, and process conditions.",
                    reference="Rule SW001 - Material shrinkage considerations",
                    defect_risk=DefectType.WARP,
                    probability_score=0.6
                ))

        # Check wall thickness analysis for warpage risk
        if analysis.wall_thickness:
            wt = analysis.wall_thickness
            if wt.variation_ratio and wt.variation_ratio > 2.0:
                exceptions.append(MoldingException(
                    exception_id=str(uuid.uuid4()),
                    severity=ExceptionSeverity.WARNING,
                    category=ExceptionCategory.SHRINKAGE_WARPAGE,
                    title=f"Non-uniform wall thickness - warpage risk",
                    description=f"Part has wall thickness variation ratio of {wt.variation_ratio:.1f}:1 "
                               f"(min: {wt.minimum_mm}mm, max: {wt.maximum_mm}mm). "
                               f"Non-uniform walls cause differential shrinkage and warpage.",
                    current_specification=f"Wall thickness range: {wt.minimum_mm}mm - {wt.maximum_mm}mm",
                    recommended_change=f"Reduce variation to <2:1 ratio. Transition gradually between thick and thin sections.",
                    reasoning="Thick sections shrink more than thin sections, creating internal stress and warpage. "
                             "Aim for uniform wall thickness throughout part.",
                    reference="Rule SW002 - Wall thickness uniformity",
                    defect_risk=DefectType.WARP,
                    probability_score=0.7
                ))

        return exceptions

    def _check_press_capabilities(self, analysis: DrawingAnalysis) -> List[MoldingException]:
        """Validate part can be molded on available presses."""
        exceptions = []

        # This requires loading plant_capabilities.json
        # For now, implement basic heuristics
        # TODO: Load actual plant capabilities from data/plant_capabilities.json

        # Estimate part volume/weight to check if press is adequate
        # Look for overall dimensions
        overall_dims = [
            d for d in analysis.dimensions
            if any(kw in d.feature.lower() for kw in ["overall", "length", "width", "height", "diameter"])
        ]

        if len(overall_dims) >= 2:
            # Rough volume estimate (very simplified)
            dim_values_mm = []
            for dim in overall_dims[:3]:  # Max 3 dimensions
                val_mm = dim.value if dim.unit == "mm" else dim.value * 25.4
                dim_values_mm.append(val_mm)

            if len(dim_values_mm) >= 2:
                # Calculate projected area (for tonnage estimate)
                projected_area_cm2 = (dim_values_mm[0] * dim_values_mm[1]) / 100

                # Rule of thumb: 2-5 tons per square inch of projected area
                # Converting: 1 in² ≈ 6.45 cm²
                projected_area_in2 = projected_area_cm2 / 6.45
                estimated_tonnage_min = projected_area_in2 * 2
                estimated_tonnage_max = projected_area_in2 * 5

                # Check against typical small-medium shop capabilities (35-150 tons)
                if estimated_tonnage_min > 150:
                    exceptions.append(MoldingException(
                        exception_id=str(uuid.uuid4()),
                        severity=ExceptionSeverity.CRITICAL,
                        category=ExceptionCategory.PRESS_CAPABILITY,
                        title=f"Part may exceed press capacity",
                        description=f"Based on projected area (~{projected_area_cm2:.0f} cm²), "
                                   f"estimated required tonnage is {estimated_tonnage_min:.0f}-{estimated_tonnage_max:.0f} tons. "
                                   f"This may exceed available press capacity.",
                        current_specification=f"Projected area: ~{projected_area_cm2:.0f} cm²",
                        recommended_change="Verify press capacity with plant. May need to reduce part size or split into multiple components.",
                        reasoning="Insufficient press tonnage leads to flash, short shots, or mold damage. "
                                 "Tonnage requirement is proportional to projected area and injection pressure.",
                        reference="Rule PC001 - Press tonnage requirements"
                    ))

        return exceptions

    def _generate_summary(self, exceptions: List[MoldingException]) -> ExceptionSummary:
        """Generate summary statistics."""
        critical = len([e for e in exceptions if e.severity == ExceptionSeverity.CRITICAL])
        warning = len([e for e in exceptions if e.severity == ExceptionSeverity.WARNING])
        info = len([e for e in exceptions if e.severity == ExceptionSeverity.INFO])

        categories = {}
        for exc in exceptions:
            categories[exc.category.value] = categories.get(exc.category.value, 0) + 1

        # Determine if can proceed
        can_proceed = critical == 0

        # Determine overall risk
        if critical > 0:
            risk = "high"
        elif warning > 3:
            risk = "medium"
        else:
            risk = "low"

        return ExceptionSummary(
            total_exceptions=len(exceptions),
            critical_count=critical,
            warning_count=warning,
            info_count=info,
            exceptions_by_category=categories,
            can_proceed=can_proceed,
            overall_risk_level=risk
        )

    def _generate_executive_summary(
        self,
        analysis: DrawingAnalysis,
        exceptions: List[MoldingException],
        summary: ExceptionSummary
    ) -> str:
        """Generate executive summary text for report."""
        critical_items = [e for e in exceptions if e.severity == ExceptionSeverity.CRITICAL]

        if not exceptions:
            return (
                f"Part '{analysis.part_id or 'Unknown'}' has been analyzed and no critical "
                f"manufacturability issues were found. The part appears feasible for injection molding "
                f"as specified."
            )

        summary_text = f"""
Part '{analysis.part_id or 'Unknown'}' Analysis Summary:

Total Exceptions Found: {summary.total_exceptions}
- Critical Issues: {summary.critical_count} (must be addressed before proceeding)
- Warnings: {summary.warning_count} (recommend review)
- Information: {summary.info_count} (best practice suggestions)

Overall Risk Level: {summary.overall_risk_level.upper()}
Can Proceed: {'NO - Critical issues must be resolved' if not summary.can_proceed else 'YES - with noted warnings'}

""".strip()

        if critical_items:
            summary_text += "\n\nCritical Issues Requiring Client Sign-Off:\n"
            for idx, exc in enumerate(critical_items, 1):
                summary_text += f"{idx}. {exc.title}\n   → {exc.recommended_change}\n"

        return summary_text

    def _generate_action_items(self, exceptions: List[MoldingException]) -> List[str]:
        """Generate list of action items from exceptions."""
        action_items = []

        # Group by severity
        critical = [e for e in exceptions if e.severity == ExceptionSeverity.CRITICAL]
        warnings = [e for e in exceptions if e.severity == ExceptionSeverity.WARNING]

        # Add critical actions
        for exc in critical:
            action_items.append(
                f"[CRITICAL] {exc.title}: {exc.recommended_change}"
            )

        # Add top warnings
        for exc in warnings[:5]:  # Limit to top 5 warnings
            action_items.append(
                f"[WARNING] {exc.title}: {exc.recommended_change}"
            )

        # Add general recommendation
        if len(exceptions) > 0:
            action_items.append(
                "Review detailed report for complete analysis and evidence (page numbers, bounding boxes)"
            )

        return action_items
