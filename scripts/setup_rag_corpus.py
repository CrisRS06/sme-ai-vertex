#!/usr/bin/env python3
"""
Setup Vertex AI RAG Corpus for Knowledge Base Grounding
This is REQUIRED for production use.

Creates a RAG corpus for storing and retrieving manuals.
"""
import os
import sys
import vertexai
from vertexai.preview import rag
from google.cloud import aiplatform

def setup_rag_corpus(project_id: str, location: str = "us-central1"):
    """
    Create Vertex AI RAG corpus for knowledge base grounding.

    Args:
        project_id: GCP project ID
        location: GCP region

    Returns:
        RAG corpus resource name
    """
    print("=" * 60)
    print("Setting up Vertex AI RAG Corpus")
    print(f"Project: {project_id}")
    print(f"Location: {location}")
    print("=" * 60)

    # Initialize Vertex AI
    print("\nInitializing Vertex AI...")
    vertexai.init(project=project_id, location=location)
    aiplatform.init(project=project_id, location=location)

    print("✓ Vertex AI initialized")

    # Check if corpus already exists
    print("\nChecking for existing RAG corpus...")
    try:
        existing_corpora = rag.list_corpora()

        for corpus in existing_corpora:
            if "manuals" in corpus.display_name.lower():
                print(f"✓ Found existing corpus: {corpus.display_name}")
                print(f"  Resource name: {corpus.name}")
                return corpus.name
    except Exception as e:
        print(f"Note: Could not list existing corpora: {e}")

    # Create new corpus
    print("\nCreating new RAG corpus...")

    try:
        # Create corpus
        corpus = rag.create_corpus(
            display_name="Molding Manuals Knowledge Base",
            description="Knowledge base for injection molding manuals, specifications, and best practices"
        )

        print("✓ RAG corpus created successfully!")
        print(f"  Corpus name: {corpus.name}")
        print(f"  Display name: {corpus.display_name}")

        return corpus.name

    except Exception as e:
        print(f"\n✗ Error creating RAG corpus: {e}")
        print("\nAlternative: Use Vertex AI Search (Discovery Engine) via Console:")
        print(f"  1. Go to: https://console.cloud.google.com/gen-app-builder/engines?project={project_id}")
        print("  2. Click 'Create App'")
        print("  3. Choose 'Search' type")
        print("  4. Create unstructured data store")
        print("  5. Use the data store ID in RAG_DATA_STORE_ID")
        raise


def main():
    """Main entry point."""
    if len(sys.argv) < 2:
        print("Error: PROJECT_ID is required")
        print("Usage: python setup_rag_corpus.py PROJECT_ID [LOCATION]")
        print("Example: python setup_rag_corpus.py sustained-truck-408014 us-central1")
        sys.exit(1)

    project_id = sys.argv[1]
    location = sys.argv[2] if len(sys.argv) > 2 else "us-central1"

    try:
        corpus_name = setup_rag_corpus(project_id, location)

        print("\n" + "=" * 60)
        print("✓ RAG Corpus Setup Complete!")
        print("=" * 60)
        print()
        print("RAG Corpus Resource Name:")
        print(corpus_name)
        print()
        print("Add this to your .env file:")
        print(f"RAG_DATA_STORE_ID={corpus_name}")
        print("ENABLE_GROUNDING=true")
        print()
        print("=" * 60)
        print("Next Steps:")
        print("=" * 60)
        print()
        print("1. Add RAG_DATA_STORE_ID to .env")
        print("2. Upload manuals using the Knowledge Base API:")
        print()
        print("   # Via Python API")
        print("   from src.services.knowledgebase_service import KnowledgeBaseService")
        print("   kb = KnowledgeBaseService()")
        print("   kb.upload_document('manual.pdf', 'manual')")
        print()
        print("   # Or via REST API")
        print("   curl -X POST http://localhost:8080/knowledgebase/upload \\")
        print("     -F 'file=@manual.pdf' \\")
        print("     -F 'document_type=manual'")
        print()
        print("3. Test with chat endpoint")
        print()
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ Setup failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
