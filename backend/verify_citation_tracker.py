#!/usr/bin/env python3
"""
Quick verification script for citation_tracker module.
Runs key tests without pytest dependency.
"""

from datetime import datetime
from app.services.citation_tracker import Citation, CitationManager

def test_citation_creation():
    """Test basic Citation creation."""
    print("\n[TEST 1] Citation Creation")
    
    # Minimal
    c1 = Citation(source="Database")
    assert c1.source == "Database"
    print("  ✓ Minimal citation created")
    
    # Full
    now = datetime.now()
    c2 = Citation(
        source="API",
        source_url="https://example.com",
        retrieval_date=now,
        confidence_score=0.95,
        data_age_hours=24
    )
    assert c2.source == "API"
    assert c2.confidence_score == 0.95
    print("  ✓ Full citation created")


def test_citation_validation():
    """Test Citation validation."""
    print("\n[TEST 2] Citation Validation")
    
    # Valid confidence
    Citation(source="Test", confidence_score=0.5)
    print("  ✓ Valid confidence score accepted")
    
    # Invalid confidence
    try:
        Citation(source="Test", confidence_score=1.5)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  ✓ Invalid confidence score rejected")
    
    # Invalid data age
    try:
        Citation(source="Test", data_age_hours=-1)
        assert False, "Should have raised ValueError"
    except ValueError:
        print("  ✓ Negative data_age_hours rejected")


def test_citation_to_dict():
    """Test Citation.to_dict()."""
    print("\n[TEST 3] Citation to_dict()")
    
    c = Citation(
        source="Source",
        source_url="https://example.com",
        confidence_score=0.9,
        data_age_hours=12
    )
    d = c.to_dict()
    
    assert d["source"] == "Source"
    assert d["source_url"] == "https://example.com"
    assert d["confidence_score"] == 0.9
    assert d["data_age_hours"] == 12
    assert "retrieval_date" in d
    print("  ✓ Citation correctly converted to dict")


def test_manager_creation():
    """Test CitationManager basic operations."""
    print("\n[TEST 4] CitationManager Creation")
    
    manager = CitationManager()
    
    # Create citation
    c = manager.create_citation(
        source="Test DB",
        confidence_score=0.88
    )
    assert c.source == "Test DB"
    print("  ✓ Citation created via manager")
    
    # Cache verification
    assert len(manager._citations_cache) == 1
    print("  ✓ Citation cached internally")


def test_attach_to_chunk():
    """Test attaching citations to chunks."""
    print("\n[TEST 5] Attach Citation to Chunk")
    
    manager = CitationManager()
    
    chunk = {
        "id": "test_1",
        "text": "Test content",
        "category": "test"
    }
    
    citation = manager.create_citation(source="Source A", confidence_score=0.92)
    cited_chunk = manager.attach_citation_to_chunk(chunk, citation)
    
    # Original fields preserved
    assert cited_chunk["id"] == "test_1"
    assert cited_chunk["text"] == "Test content"
    print("  ✓ Original chunk fields preserved")
    
    # Citation added
    assert "citation" in cited_chunk
    assert cited_chunk["citation"]["source"] == "Source A"
    print("  ✓ Citation attached to chunk")
    
    # Original unchanged
    assert "citation" not in chunk
    print("  ✓ Original chunk not mutated")


def test_batch_add_citations():
    """Test batch citation attachment."""
    print("\n[TEST 6] Batch Add Citations")
    
    manager = CitationManager()
    
    chunks = [
        {"text": "Career path", "id": "1"},
        {"text": "Interview prep", "id": "2"},
        {"text": "Learning resources", "id": "3"}
    ]
    
    citations = [
        manager.create_citation(source="DB1"),
        manager.create_citation(source="DB2"),
        None  # Skip third
    ]
    
    result = manager.add_citations_to_chunks(chunks, citations)
    
    assert len(result) == 3
    assert "citation" in result[0]
    assert "citation" in result[1]
    assert "citation" not in result[2]
    print("  ✓ Batch citations applied correctly")


def test_citation_summary():
    """Test citation summary statistics."""
    print("\n[TEST 7] Citation Summary")
    
    manager = CitationManager()
    
    chunks = [
        {"text": "Chunk 1", "citation": {"source": "DB", "confidence_score": 0.90}},
        {"text": "Chunk 2", "citation": {"source": "DB", "confidence_score": 0.80}},
        {"text": "Chunk 3"},  # No citation
    ]
    
    summary = manager.get_citation_summary(chunks)
    
    assert summary["total_chunks"] == 3
    assert summary["cited_chunks"] == 2
    assert summary["uncited_chunks"] == 1
    assert summary["citation_rate"] == 66.7
    assert summary["avg_confidence"] == 0.85
    print("  ✓ Citation summary calculated correctly")
    
    # Print summary
    print(f"    - Citation rate: {summary['citation_rate']}%")
    print(f"    - Avg confidence: {summary['avg_confidence']}")
    print(f"    - Unique sources: {summary['unique_sources']}")


def test_backward_compatibility():
    """Test backward compatibility with existing chunks."""
    print("\n[TEST 8] Backward Compatibility")
    
    manager = CitationManager()
    
    # Chunks without citation field
    chunks = [
        {"text": "No citation here", "category": "test"},
        {"text": "Another chunk", "tags": ["tag1", "tag2"]}
    ]
    
    # Should process without errors
    summary = manager.get_citation_summary(chunks)
    assert summary["cited_chunks"] == 0
    print("  ✓ Chunks without citations work fine")
    
    # Attach citations to existing chunks
    result = manager.add_citations_to_chunks(
        chunks,
        [manager.create_citation(source="S1"), manager.create_citation(source="S2")]
    )
    
    # Original fields still present
    assert result[0]["text"] == chunks[0]["text"]
    assert result[1]["tags"] == chunks[1]["tags"]
    print("  ✓ Existing chunk structure preserved")


def main():
    """Run all tests."""
    print("=" * 70)
    print("CITATION TRACKER MODULE VERIFICATION")
    print("=" * 70)
    
    try:
        test_citation_creation()
        test_citation_validation()
        test_citation_to_dict()
        test_manager_creation()
        test_attach_to_chunk()
        test_batch_add_citations()
        test_citation_summary()
        test_backward_compatibility()
        
        print("\n" + "=" * 70)
        print("✓ ALL TESTS PASSED (8/8)")
        print("=" * 70)
        return 0
    
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())
