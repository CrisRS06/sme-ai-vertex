"""
Configurable prompts for AI analysis.
These can be modified via API without redeploying.
"""
from typing import Dict
import json
import os
from pathlib import Path

# Default prompts configuration
DEFAULT_PROMPTS = {
    "pdf_extraction": {
        "name": "PDF Technical Extraction",
        "description": "Prompt used to extract technical specifications from uploaded PDFs",
        "prompt": """Eres un experto en análisis de planos técnicos para moldeo por inyección.

Analiza el plano PDF cuidadosamente y extrae TODA la información técnica relevante:

📏 DIMENSIONES:
- Dimensiones principales de la pieza (largo, ancho, alto)
- Espesores de pared (mínimo, máximo, promedio)
- Radios, chaflanes y características geométricas
- Profundidades de cavidades

🔧 ESPECIFICACIONES TÉCNICAS:
- Material especificado (ABS, PP, PC, PA, POM, etc.)
- Tolerancias dimensionales (generales y específicas)
- Acabado superficial requerido
- Notas técnicas importantes
- Tratamientos especiales

📐 GEOMETRÍA Y MOLDEO:
- Ángulos de desmoldeo especificados
- Undercuts o características que compliquen el desmoldeo
- Nervaduras y refuerzos (cantidad, dimensiones)
- Insertos metálicos o roscados
- Líneas de partición sugeridas

🎯 ÁREAS CRÍTICAS:
- Zonas de alta precisión
- Características que requieren atención especial
- Posibles problemas de manufactura

Presenta la información de forma estructurada, clara y detallada.
Si algo no está especificado en el plano, indícalo claramente."""
    },

    "kb_analysis": {
        "name": "Knowledge Base Analysis",
        "description": "Prompt used to analyze extracted specs against Knowledge Base",
        "prompt": """Basándote en las especificaciones técnicas extraídas del plano, proporciona un análisis COMPLETO de viabilidad de moldeo por inyección.

ESPECIFICACIONES DEL PLANO:
{extracted_specs}

Tu análisis debe incluir:

✅ VIABILIDAD GENERAL:
- ¿Es viable fabricar esta pieza por moldeo por inyección?
- Clasificación: VIABLE / VIABLE CON MODIFICACIONES / NO RECOMENDADO

📏 ANÁLISIS DE ESPESORES:
- ¿Los espesores de pared son adecuados para el material especificado?
- Comparar con rangos recomendados según mejores prácticas
- Identificar riesgos: marcas de hundimiento, deformación, tiempo de ciclo

🎯 TOLERANCIAS:
- ¿Las tolerancias especificadas son alcanzables?
- Identificar tolerancias críticas que requieren atención especial
- Sugerencias de post-procesado si es necesario

🔧 MATERIAL:
- ¿El material es apropiado para las dimensiones y uso de la pieza?
- Consideraciones de procesabilidad
- Alternativas si aplica

📐 GEOMETRÍA Y DESMOLDEO:
- Validar ángulos de desmoldeo
- Analizar undercuts y características complejas
- Sugerencias para facilitar el desmoldeo

⚠️ RIESGOS Y DESAFÍOS:
- Identificar posibles problemas de manufactura
- Áreas que requieren simulación adicional
- Consideraciones de costo

💡 RECOMENDACIONES:
- Mejoras de diseño sugeridas
- Optimizaciones para reducir costo
- Mejores prácticas aplicables

IMPORTANTE:
- Fundamenta TODAS tus afirmaciones con información de la Knowledge Base
- Cita las fuentes específicas cuando hagas recomendaciones
- Sé específico con números y rangos
- Si algo no está en la KB, indícalo claramente"""
    },

    "unified_response": {
        "name": "Unified Response Template",
        "description": "Template for combining extraction + analysis in single response",
        "prompt": """He analizado tu plano técnico completamente. Aquí está mi evaluación:

═══════════════════════════════════════════════════════════════════
📋 ESPECIFICACIONES IDENTIFICADAS
═══════════════════════════════════════════════════════════════════

{extraction_result}

═══════════════════════════════════════════════════════════════════
✅ ANÁLISIS DE VIABILIDAD DE MOLDEO
═══════════════════════════════════════════════════════════════════

{kb_analysis_result}

═══════════════════════════════════════════════════════════════════
💬 CONCLUSIÓN
═══════════════════════════════════════════════════════════════════

{conclusion}"""
    }
}


class PromptsConfig:
    """Manages configurable prompts with persistence."""

    def __init__(self, config_file: str = "config/prompts_config.json"):
        self.config_file = Path(config_file)
        self.prompts = self._load_prompts()

    def _load_prompts(self) -> Dict:
        """Load prompts from file or use defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading prompts config: {e}, using defaults")
                return DEFAULT_PROMPTS.copy()
        return DEFAULT_PROMPTS.copy()

    def save_prompts(self) -> bool:
        """Save current prompts to file."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.prompts, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving prompts config: {e}")
            return False

    def get_prompt(self, prompt_key: str) -> str:
        """Get a specific prompt by key."""
        if prompt_key in self.prompts:
            return self.prompts[prompt_key]["prompt"]
        return DEFAULT_PROMPTS.get(prompt_key, {}).get("prompt", "")

    def get_all_prompts(self) -> Dict:
        """Get all prompts configuration."""
        return self.prompts.copy()

    def update_prompt(self, prompt_key: str, new_prompt: str) -> bool:
        """Update a specific prompt."""
        if prompt_key in self.prompts:
            self.prompts[prompt_key]["prompt"] = new_prompt
            return self.save_prompts()
        return False

    def reset_to_defaults(self) -> bool:
        """Reset all prompts to defaults."""
        self.prompts = DEFAULT_PROMPTS.copy()
        return self.save_prompts()

    def get_prompt_metadata(self, prompt_key: str) -> Dict:
        """Get metadata for a prompt."""
        if prompt_key in self.prompts:
            return {
                "name": self.prompts[prompt_key].get("name", ""),
                "description": self.prompts[prompt_key].get("description", "")
            }
        return {}


# Global instance
prompts_config = PromptsConfig()
