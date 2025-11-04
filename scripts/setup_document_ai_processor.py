#!/usr/bin/env python3
"""
Setup Document AI Processor for OCR Fallback
This is REQUIRED for production use.

Creates a Form Parser processor for extracting dimensions from technical drawings.
"""
import os
import sys
from google.cloud import documentai_v1 as documentai
from google.api_core import exceptions

def setup_document_ai_processor(project_id: str, location: str = "us"):
    """
    Create Document AI processor for OCR fallback.

    Args:
        project_id: GCP project ID
        location: Document AI location (must be 'us' or 'eu')

    Returns:
        Processor ID
    """
    print("=" * 60)
    print("Setting up Document AI OCR Processor")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    print("=" * 60)

    # Initialize Document AI client
    print("\nInitializing Document AI...")
    parent = f"projects/{project_id}/locations/{location}"
    client = documentai.DocumentProcessorServiceClient()

    print("✓ Document AI client initialized")

    # Check if processor already exists
    print("\nChecking for existing processors...")
    try:
        processors = client.list_processors(parent=parent)

        for processor in processors:
            if "Drawing" in processor.display_name or "OCR" in processor.display_name:
                print(f"✓ Found existing processor: {processor.display_name}")
                print(f"  Processor name: {processor.name}")
                # Extract processor ID from name
                processor_id = processor.name.split("/")[-1]
                return processor_id
    except Exception as e:
        print(f"Note: Could not list existing processors: {e}")

    # Create new processor
    print("\nCreating new Form Parser processor...")
    print("  (Form Parser is best for technical drawings with tables and dimensions)")

    try:
        processor = documentai.Processor(
            display_name="Drawing OCR Fallback",
            type_="FORM_PARSER_PROCESSOR",  # Best for technical drawings
        )

        created_processor = client.create_processor(
            parent=parent,
            processor=processor
        )

        print("✓ Processor created successfully!")
        print(f"  Processor name: {created_processor.name}")
        print(f"  Display name: {created_processor.display_name}")
        print(f"  Type: {created_processor.type_}")

        # Extract processor ID from name
        # Format: projects/PROJECT_ID/locations/LOCATION/processors/PROCESSOR_ID
        processor_id = created_processor.name.split("/")[-1]

        return processor_id

    except exceptions.PermissionDenied as e:
        print(f"\n✗ Permission denied: {e}")
        print("\nPlease ensure:")
        print("  1. Document AI API is enabled")
        print("  2. Service account has 'Document AI Editor' role")
        raise

    except Exception as e:
        print(f"\n✗ Error creating processor: {e}")
        print("\nAlternative: Create processor via Console:")
        print(f"  1. Go to: https://console.cloud.google.com/ai/document-ai/processors?project={project_id}")
        print("  2. Click 'Create Processor'")
        print("  3. Choose 'Form Parser'")
        print("  4. Name it 'Drawing OCR Fallback'")
        print("  5. Copy the Processor ID")
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Error: PROJECT_ID is required")
        print("Usage: python setup_document_ai_processor.py PROJECT_ID [LOCATION]")
        print("Example: python setup_document_ai_processor.py sustained-truck-408014 us")
        sys.exit(1)

    project_id = sys.argv[1]
    location = sys.argv[2] if len(sys.argv) > 2 else "us"

    # Validate location
    if location not in ["us", "eu"]:
        print(f"Warning: Location '{location}' is not standard.")
        print("Document AI typically uses 'us' or 'eu'.")
        print("Using 'us' as default...")
        location = "us"

    try:
        processor_id = setup_document_ai_processor(project_id, location)

        print("\n" + "=" * 60)
        print("✓ Document AI Processor Setup Complete!")
        print("=" * 60)
        print()
        print("Processor ID:")
        print(processor_id)
        print()
        print("Add this to your .env file:")
        print(f"DOCUMENT_AI_PROCESSOR_ID={processor_id}")
        print("ENABLE_DOCUMENT_AI_FALLBACK=true")
        print("OCR_CONFIDENCE_THRESHOLD=0.7")
        print()
        print("=" * 60)
        print("How it works:")
        print("=" * 60)
        print()
        print("1. VLM (Gemini 2.5 Flash) analyzes drawings")
        print("2. If dimension confidence < 0.7 → OCR fallback triggers")
        print("3. Document AI extracts text with high precision")
        print("4. Results are merged (keep high-confidence VLM + OCR enhancements)")
        print("5. Metrics track OCR usage and recovery rate")
        print()
        print("This ensures NO information loss from microtext!")
        print()
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
