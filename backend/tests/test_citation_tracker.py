"""
Unit Tests for Citation Tracker Module
=======================================
Comprehensive test suite for citation metadata layer.
Tests: Citation creation, validation, chunk attachment, batch processing,
and citation summary statistics.

Run with: pytest tests/test_citation_tracker.py -v
"""

import pytest
from datetime import datetime, timedelta
from app.services.citation_tracker import Citation, CitationManager


# ─────────────────────────────────────────────────────────────────────────────
# FIXTURE: CitationManager instance
# ─────────────────────────────────────────────────────────────────────────────

@pytest.fixture
def manager():
    """Provide a fresh CitationManager for each test."""
    return CitationManager()


@pytest.fixture
def sample_chunks():
    """Sample knowledge chunks for testing."""
    return [
        {
            "id": "ai_engineer_path",
            "text": "AI Engineer career path requires Python, ML, Deep Learning...",
            "category": "career_path",
            "tags": ["AI", "career", "learning"]
        },
        {
            "id": "fullstack_dev",
            "text": "Full Stack Developer combines frontend, backend, and DevOps...",
            "category": "career_path",
            "tags": ["web", "fullstack"]
        },
        {
            "id": "interview_tips",
            "text": "Technical interview preparation: DSA, System Design, Behavioral...",
            "category": "interview",
            "tags": ["interview", "preparation"]
        }
    ]


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 1: Citation Dataclass Creation and Validation
# ─────────────────────────────────────────────────────────────────────────────

class TestCitationCreation:
    """Test Citation dataclass creation and validation."""

    def test_citation_minimal_creation(self):
        """Citation should be creatable with only source field."""
        citation = Citation(source="Test Database")
        assert citation.source == "Test Database"
        assert citation.source_url is None
        assert citation.retrieval_date is not None  # Auto-filled in factory
        assert citation.confidence_score is None
        assert citation.data_age_hours is None

    def test_citation_full_creation(self):
        """Citation should support all optional fields."""
        now = datetime.now()
        citation = Citation(
            source="API Source",
            source_url="https://example.com/data",
            retrieval_date=now,
            confidence_score=0.95,
            data_age_hours=48
        )
        assert citation.source == "API Source"
        assert citation.source_url == "https://example.com/data"
        assert citation.retrieval_date == now
        assert citation.confidence_score == 0.95
        assert citation.data_age_hours == 48

    def test_citation_empty_source_raises_error(self):
        """Citation should reject empty source string."""
        with pytest.raises(ValueError, match="source.*must be a non-empty string"):
            Citation(source="")

    def test_citation_none_source_raises_error(self):
        """Citation should reject None source."""
        with pytest.raises(ValueError, match="source.*must be a non-empty string"):
            Citation(source=None)

    def test_citation_confidence_score_validation(self):
        """Citation should validate confidence_score is 0.0-1.0."""
        # Valid boundaries
        Citation(source="Test", confidence_score=0.0)
        Citation(source="Test", confidence_score=1.0)
        Citation(source="Test", confidence_score=0.5)
        
        # Invalid values
        with pytest.raises(ValueError, match="confidence_score.*0.0 and 1.0"):
            Citation(source="Test", confidence_score=1.5)
        
        with pytest.raises(ValueError, match="confidence_score.*0.0 and 1.0"):
            Citation(source="Test", confidence_score=-0.1)

    def test_citation_data_age_validation(self):
        """Citation should reject negative data_age_hours."""
        # Valid
        Citation(source="Test", data_age_hours=0)
        Citation(source="Test", data_age_hours=72)
        
        # Invalid
        with pytest.raises(ValueError, match="data_age_hours.*cannot be negative"):
            Citation(source="Test", data_age_hours=-1)


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 2: Citation to Dictionary Conversion
# ─────────────────────────────────────────────────────────────────────────────

class TestCitationConversion:
    """Test Citation to_dict() conversion."""

    def test_to_dict_minimal(self):
        """to_dict should include only non-None fields."""
        citation = Citation(source="Simple Source")
        result = citation.to_dict()
        
        assert result["source"] == "Simple Source"
        assert "source_url" not in result
        assert "confidence_score" not in result
        assert "data_age_hours" not in result

    def test_to_dict_with_all_fields(self):
        """to_dict should include all fields when provided."""
        now = datetime.now()
        citation = Citation(
            source="Complete Source",
            source_url="https://example.com",
            retrieval_date=now,
            confidence_score=0.85,
            data_age_hours=24
        )
        result = citation.to_dict()
        
        assert result["source"] == "Complete Source"
        assert result["source_url"] == "https://example.com"
        assert result["retrieval_date"] == now.isoformat()
        assert result["confidence_score"] == 0.85
        assert result["data_age_hours"] == 24

    def test_to_dict_retrieval_date_iso_format(self):
        """to_dict should convert datetime to ISO format string."""
        citation = Citation(
            source="Test",
            retrieval_date=datetime(2024, 1, 15, 10, 30, 45)
        )
        result = citation.to_dict()
        
        assert isinstance(result["retrieval_date"], str)
        assert "2024-01-15" in result["retrieval_date"]


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 3: CitationManager - Citation Creation
# ─────────────────────────────────────────────────────────────────────────────

class TestCitationManagerCreation:
    """Test CitationManager.create_citation()."""

    def test_create_citation_minimal(self, manager):
        """Manager should create citation with source only."""
        citation = manager.create_citation(source="Test Database")
        assert citation.source == "Test Database"
        assert citation.retrieval_date is not None

    def test_create_citation_full_params(self, manager):
        """Manager should create citation with all parameters."""
        citation = manager.create_citation(
            source="Complete Source",
            source_url="https://example.com",
            confidence_score=0.92,
            data_age_hours=12
        )
        assert citation.source == "Complete Source"
        assert citation.source_url == "https://example.com"
        assert citation.confidence_score == 0.92
        assert citation.data_age_hours == 12

    def test_create_citation_caches_internally(self, manager):
        """Manager should cache created citations."""
        citation1 = manager.create_citation(source="First")
        citation2 = manager.create_citation(source="Second")
        
        # Should have 2 cached items
        assert len(manager._citations_cache) == 2

    def test_create_citation_auto_timestamp(self, manager):
        """Manager should auto-set retrieval_date if not provided."""
        citation = manager.create_citation(source="Test")
        assert citation.retrieval_date is not None
        
        # Should be recent (within 5 seconds)
        time_diff = datetime.now() - citation.retrieval_date
        assert time_diff.total_seconds() < 5


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 4: CitationManager - Chunk Attachment
# ─────────────────────────────────────────────────────────────────────────────

class TestCitationAttachment:
    """Test CitationManager.attach_citation_to_chunk()."""

    def test_attach_citation_single_chunk(self, manager, sample_chunks):
        """Manager should attach citation to chunk with all original fields."""
        chunk = sample_chunks[0]
        citation = manager.create_citation(
            source="Career Database",
            confidence_score=0.90
        )
        
        cited_chunk = manager.attach_citation_to_chunk(chunk, citation)
        
        # Original fields preserved
        assert cited_chunk["id"] == "ai_engineer_path"
        assert cited_chunk["category"] == "career_path"
        assert "Python" in cited_chunk["text"]
        
        # Citation added
        assert "citation" in cited_chunk
        assert cited_chunk["citation"]["source"] == "Career Database"
        assert cited_chunk["citation"]["confidence_score"] == 0.90

    def test_attach_citation_none_chunk(self, manager):
        """Manager should handle None chunk gracefully."""
        citation = manager.create_citation(source="Test")
        result = manager.attach_citation_to_chunk(None, citation)
        
        assert result == {}

    def test_attach_citation_none_citation(self, manager, sample_chunks):
        """Manager should handle None citation gracefully."""
        chunk = sample_chunks[0].copy()
        original_id = chunk["id"]
        
        cited_chunk = manager.attach_citation_to_chunk(chunk, None)
        
        # Chunk preserved but no citation added
        assert cited_chunk["id"] == original_id
        assert "citation" not in cited_chunk

    def test_attach_citation_preserves_original(self, manager, sample_chunks):
        """Manager should not mutate original chunk."""
        original_chunk = sample_chunks[0]
        citation = manager.create_citation(source="Test")
        
        cited_chunk = manager.attach_citation_to_chunk(original_chunk, citation)
        
        # Original should be unchanged
        assert "citation" not in original_chunk
        
        # New chunk should have citation
        assert "citation" in cited_chunk


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 5: CitationManager - Batch Processing
# ─────────────────────────────────────────────────────────────────────────────

class TestBatchCitationProcessing:
    """Test CitationManager.add_citations_to_chunks()."""

    def test_batch_add_citations_matching_length(self, manager, sample_chunks):
        """Manager should add citations when lists match in length."""
        citations = [
            manager.create_citation(source="DB1", confidence_score=0.90),
            manager.create_citation(source="DB2", confidence_score=0.85),
            manager.create_citation(source="API", confidence_score=0.92)
        ]
        
        result = manager.add_citations_to_chunks(sample_chunks, citations)
        
        assert len(result) == 3
        assert result[0]["citation"]["source"] == "DB1"
        assert result[1]["citation"]["source"] == "DB2"
        assert result[2]["citation"]["source"] == "API"

    def test_batch_add_citations_fewer_citations(self, manager, sample_chunks):
        """Manager should handle fewer citations than chunks."""
        citations = [
            manager.create_citation(source="DB1"),
            manager.create_citation(source="DB2")
        ]
        
        result = manager.add_citations_to_chunks(sample_chunks, citations)
        
        assert len(result) == 3
        assert "citation" in result[0]
        assert "citation" in result[1]
        assert "citation" not in result[2]

    def test_batch_add_citations_more_citations(self, manager, sample_chunks):
        """Manager should ignore extra citations beyond chunk count."""
        citations = [
            manager.create_citation(source="DB1"),
            manager.create_citation(source="DB2"),
            manager.create_citation(source="DB3"),
            manager.create_citation(source="DB4")  # Extra
        ]
        
        result = manager.add_citations_to_chunks(sample_chunks, citations)
        
        assert len(result) == 3
        for chunk in result:
            assert "citation" in chunk

    def test_batch_add_citations_with_none_values(self, manager, sample_chunks):
        """Manager should skip None values in citation list."""
        citations = [
            manager.create_citation(source="DB1"),
            None,
            manager.create_citation(source="DB3")
        ]
        
        result = manager.add_citations_to_chunks(sample_chunks, citations)
        
        assert len(result) == 3
        assert "citation" in result[0]
        assert "citation" not in result[1]
        assert "citation" in result[2]

    def test_batch_add_citations_empty_chunk_list(self, manager):
        """Manager should handle empty chunk list."""
        citations = [manager.create_citation(source="Test")]
        result = manager.add_citations_to_chunks([], citations)
        
        assert result == []

    def test_batch_add_citations_none_citation_list(self, manager, sample_chunks):
        """Manager should handle None citation list."""
        result = manager.add_citations_to_chunks(sample_chunks, None)
        
        assert len(result) == 3
        for chunk in result:
            assert "citation" not in chunk


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 6: Citation Summary Statistics
# ─────────────────────────────────────────────────────────────────────────────

class TestCitationSummary:
    """Test CitationManager.get_citation_summary()."""

    def test_citation_summary_all_cited(self, manager, sample_chunks):
        """Summary should show 100% citation rate when all cited."""
        citations = [
            manager.create_citation(source="DB", confidence_score=0.90),
            manager.create_citation(source="API", confidence_score=0.88),
            manager.create_citation(source="Cache", confidence_score=0.95)
        ]
        
        cited_chunks = manager.add_citations_to_chunks(sample_chunks, citations)
        summary = manager.get_citation_summary(cited_chunks)
        
        assert summary["total_chunks"] == 3
        assert summary["cited_chunks"] == 3
        assert summary["uncited_chunks"] == 0
        assert summary["citation_rate"] == 100.0
        assert summary["unique_sources"] == 3

    def test_citation_summary_partial_cited(self, manager, sample_chunks):
        """Summary should show correct rate for partial citations."""
        citations = [
            manager.create_citation(source="DB", confidence_score=0.90),
            None,
            manager.create_citation(source="API", confidence_score=0.80)
        ]
        
        cited_chunks = manager.add_citations_to_chunks(sample_chunks, citations)
        summary = manager.get_citation_summary(cited_chunks)
        
        assert summary["total_chunks"] == 3
        assert summary["cited_chunks"] == 2
        assert summary["uncited_chunks"] == 1
        assert summary["citation_rate"] == 66.7

    def test_citation_summary_no_citations(self, manager, sample_chunks):
        """Summary should show 0% when no citations."""
        summary = manager.get_citation_summary(sample_chunks)
        
        assert summary["total_chunks"] == 3
        assert summary["cited_chunks"] == 0
        assert summary["uncited_chunks"] == 3
        assert summary["citation_rate"] == 0.0
        assert summary["avg_confidence"] is None

    def test_citation_summary_average_confidence(self, manager, sample_chunks):
        """Summary should calculate average confidence correctly."""
        citations = [
            manager.create_citation(source="DB1", confidence_score=0.80),
            manager.create_citation(source="DB2", confidence_score=0.90),
            manager.create_citation(source="DB3", confidence_score=1.00)
        ]
        
        cited_chunks = manager.add_citations_to_chunks(sample_chunks, citations)
        summary = manager.get_citation_summary(cited_chunks)
        
        # Average: (0.80 + 0.90 + 1.00) / 3 = 0.90
        assert summary["avg_confidence"] == 0.9

    def test_citation_summary_source_tracking(self, manager, sample_chunks):
        """Summary should track source usage correctly."""
        citations = [
            manager.create_citation(source="Database"),
            manager.create_citation(source="Database"),
            manager.create_citation(source="API")
        ]
        
        cited_chunks = manager.add_citations_to_chunks(sample_chunks, citations)
        summary = manager.get_citation_summary(cited_chunks)
        
        assert summary["sources_used"]["Database"] == 2
        assert summary["sources_used"]["API"] == 1
        assert summary["unique_sources"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 7: Integration and Edge Cases
# ─────────────────────────────────────────────────────────────────────────────

class TestIntegration:
    """Integration tests covering real-world scenarios."""

    def test_full_workflow_single_chunk(self, manager):
        """Test complete workflow: create citation → attach to chunk."""
        # Create citation
        citation = manager.create_citation(
            source="Career Knowledge Base",
            source_url="https://skillens.ai/careers",
            confidence_score=0.94,
            data_age_hours=24
        )
        
        # Create chunk
        chunk = {
            "id": "ai_path",
            "text": "AI Engineer requires: Python, ML, Deep Learning",
            "category": "career_path",
            "tags": ["AI", "career"]
        }
        
        # Attach
        cited_chunk = manager.attach_citation_to_chunk(chunk, citation)
        
        # Verify
        assert cited_chunk["text"] == chunk["text"]
        assert cited_chunk["citation"]["source"] == "Career Knowledge Base"
        assert cited_chunk["citation"]["confidence_score"] == 0.94

    def test_full_workflow_batch_processing(self, manager, sample_chunks):
        """Test complete workflow: create multiple citations → batch attach."""
        # Create citations
        citations = [
            manager.create_citation(
                source="Database A",
                confidence_score=0.92,
                data_age_hours=12
            ),
            manager.create_citation(
                source="API B",
                confidence_score=0.87,
                data_age_hours=6
            ),
            manager.create_citation(
                source="Cache",
                confidence_score=0.99,
                data_age_hours=1
            )
        ]
        
        # Batch attach
        cited_chunks = manager.add_citations_to_chunks(sample_chunks, citations)
        
        # Get summary
        summary = manager.get_citation_summary(cited_chunks)
        
        # Verify
        assert len(cited_chunks) == 3
        assert summary["citation_rate"] == 100.0
        assert summary["avg_confidence"] == pytest.approx((0.92 + 0.87 + 0.99) / 3, rel=0.01)

    def test_mixed_cited_and_uncited_chunks(self, manager):
        """Test processing mix of cited and uncited chunks."""
        chunks = [
            {"text": "Career info", "id": "1"},
            {"text": "Interview tips", "id": "2", "citation": {"source": "Book"}},
            {"text": "Learning path", "id": "3"}
        ]
        
        summary = manager.get_citation_summary(chunks)
        
        assert summary["total_chunks"] == 3
        assert summary["cited_chunks"] == 1
        assert summary["citation_rate"] == 33.3

    def test_empty_chunk_handling(self, manager):
        """Test handling of empty/minimal chunks."""
        chunks = [
            {},  # Empty chunk
            {"text": ""},  # Empty text
            {"id": "no_text"}  # No text field
        ]
        
        citations = [
            manager.create_citation(source="Source1"),
            manager.create_citation(source="Source2"),
            manager.create_citation(source="Source3")
        ]
        
        result = manager.add_citations_to_chunks(chunks, citations)
        
        assert len(result) == 3
        for i, chunk in enumerate(result):
            assert "citation" in chunk
            assert chunk["citation"]["source"] == f"Source{i+1}"


# ─────────────────────────────────────────────────────────────────────────────
# TEST SUITE 8: Backward Compatibility
# ─────────────────────────────────────────────────────────────────────────────

class TestBackwardCompatibility:
    """Test that citation layer doesn't break existing code."""

    def test_chunks_without_citation_field_still_work(self, manager, sample_chunks):
        """Chunks without citation field should remain unchanged."""
        summary = manager.get_citation_summary(sample_chunks)
        
        # Should process without errors
        assert summary["total_chunks"] == len(sample_chunks)
        assert summary["cited_chunks"] == 0

    def test_existing_chunk_structure_preserved(self, manager, sample_chunks):
        """Attaching citation should preserve all existing chunk fields."""
        chunk = sample_chunks[0]
        original_keys = set(chunk.keys())
        
        citation = manager.create_citation(source="Test")
        cited_chunk = manager.attach_citation_to_chunk(chunk, citation)
        
        # All original keys should still exist
        for key in original_keys:
            assert key in cited_chunk
            assert cited_chunk[key] == chunk[key]

    def test_can_use_chunks_without_citation_manager(self, sample_chunks):
        """Chunks should work independently without CitationManager."""
        # Process chunks normally without manager
        for chunk in sample_chunks:
            text = chunk.get("text", "")
            category = chunk.get("category", "unknown")
            
            # Should work fine
            assert isinstance(text, str)
            assert isinstance(category, str)
