"""
Citation Tracker — RAG Citation Metadata Layer
===============================================
Manages source attribution and metadata for AI-generated responses in RAG systems.
Enables transparent citation tracking while maintaining backward compatibility
with existing chunk structure.

Features:
- Citation dataclass with source, URL, date, confidence, and age metadata
- CitationManager for injecting citations into knowledge chunks
- Seamless integration with retrieval pipeline
- Graceful handling of None/empty citations
- Comprehensive logging for audit trails

Example:
    from app.services.citation_tracker import Citation, CitationManager
    
    # Create a citation
    citation = Citation(
        source="Knowledge Base",
        source_url="https://example.com/knowledge",
        retrieval_date=datetime.now(),
        confidence_score=0.92,
        data_age_hours=48
    )
    
    # Attach to chunks
    manager = CitationManager()
    chunk = {"text": "Career AI Engineer Overview...", "category": "career_path"}
    cited_chunk = manager.attach_citation_to_chunk(chunk, citation)
    
    # Batch process
    citations = [citation1, citation2]
    chunks = [chunk1, chunk2]
    cited_chunks = manager.add_citations_to_chunks(chunks, citations)
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


@dataclass
class Citation:
    """
    Citation metadata for knowledge chunks and AI responses.
    
    Attributes:
        source (str): Source identifier (e.g., "Database", "API", "User Input")
        source_url (Optional[str]): Direct link to the source material
        retrieval_date (Optional[datetime]): When this information was retrieved
        confidence_score (Optional[float]): Confidence level (0.0-1.0) for this source
        data_age_hours (Optional[int]): How many hours old the data is
    
    Example:
        >>> citation = Citation(
        ...     source="Career Knowledge Base",
        ...     source_url="https://skillens.example.com/careers/ai-engineer",
        ...     retrieval_date=datetime.now(),
        ...     confidence_score=0.95,
        ...     data_age_hours=24
        ... )
        >>> print(citation.source)
        'Career Knowledge Base'
    """
    source: str
    source_url: Optional[str] = None
    retrieval_date: Optional[datetime] = None
    confidence_score: Optional[float] = None
    data_age_hours: Optional[int] = None

    def __post_init__(self):
        """Validate citation data after initialization."""
        if not self.source or not isinstance(self.source, str):
            raise ValueError("Citation 'source' must be a non-empty string")
        
        if self.confidence_score is not None:
            if not (0.0 <= self.confidence_score <= 1.0):
                raise ValueError("confidence_score must be between 0.0 and 1.0")
        
        if self.data_age_hours is not None:
            if self.data_age_hours < 0:
                raise ValueError("data_age_hours cannot be negative")
        
        # Auto-set retrieval_date if not provided
        if self.retrieval_date is None:
            object.__setattr__(self, 'retrieval_date', datetime.now())
        
        logger.debug(f"Citation created: source={self.source}, "
                    f"confidence={self.confidence_score}, "
                    f"age={self.data_age_hours}h")

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert citation to dictionary format.
        
        Returns:
            Dict with citation metadata (None values excluded)
        
        Example:
            >>> citation = Citation(source="DB", confidence_score=0.9)
            >>> citation.to_dict()
            {'source': 'DB', 'confidence_score': 0.9}
        """
        result = {"source": self.source}
        
        if self.source_url:
            result["source_url"] = self.source_url
        
        if self.retrieval_date:
            result["retrieval_date"] = self.retrieval_date.isoformat()
        
        if self.confidence_score is not None:
            result["confidence_score"] = self.confidence_score
        
        if self.data_age_hours is not None:
            result["data_age_hours"] = self.data_age_hours
        
        return result


class CitationManager:
    """
    Manages citation metadata injection into knowledge chunks.
    
    Handles creation, attachment, and batch processing of citations
    while maintaining backward compatibility with existing chunk structures.
    
    Attributes:
        _citations_cache (Dict): In-memory cache of created citations
    
    Example:
        >>> manager = CitationManager()
        >>> citation = manager.create_citation(
        ...     source="Career API",
        ...     confidence_score=0.88
        ... )
        >>> chunk = {"text": "Full Stack Developer path...", "category": "learning"}
        >>> cited_chunk = manager.attach_citation_to_chunk(chunk, citation)
        >>> print(cited_chunk.get("citation"))
        {'source': 'Career API', 'confidence_score': 0.88}
    """
    
    def __init__(self):
        """Initialize CitationManager with empty cache."""
        self._citations_cache: Dict[str, Citation] = {}
        logger.info("CitationManager initialized")

    def create_citation(
        self,
        source: str,
        source_url: Optional[str] = None,
        retrieval_date: Optional[datetime] = None,
        confidence_score: Optional[float] = None,
        data_age_hours: Optional[int] = None
    ) -> Citation:
        """
        Create a new citation instance.
        
        Args:
            source: Source identifier (required)
            source_url: Optional URL to the source
            retrieval_date: Optional datetime of retrieval
            confidence_score: Optional confidence level (0.0-1.0)
            data_age_hours: Optional age of data in hours
        
        Returns:
            Citation: Newly created citation object
        
        Raises:
            ValueError: If source is empty or invalid
        
        Example:
            >>> manager = CitationManager()
            >>> citation = manager.create_citation(
            ...     source="Government Database",
            ...     source_url="https://govt.in/officials",
            ...     confidence_score=0.99,
            ...     data_age_hours=72
            ... )
            >>> citation.source
            'Government Database'
        """
        citation = Citation(
            source=source,
            source_url=source_url,
            retrieval_date=retrieval_date or datetime.now(),
            confidence_score=confidence_score,
            data_age_hours=data_age_hours
        )
        
        # Cache for audit trail
        cache_key = f"{source}_{len(self._citations_cache)}"
        self._citations_cache[cache_key] = citation
        
        logger.info(f"Created citation: {source} (cached as {cache_key})")
        return citation

    def attach_citation_to_chunk(
        self,
        chunk: Dict[str, Any],
        citation: Optional[Citation] = None
    ) -> Dict[str, Any]:
        """
        Attach citation metadata to a knowledge chunk.
        
        Preserves all existing chunk fields and adds optional 'citation' field.
        Backward compatible: chunks without citations remain unchanged.
        
        Args:
            chunk: Knowledge chunk dictionary to annotate
            citation: Citation object or None
        
        Returns:
            Dict: Enhanced chunk with optional citation field
        
        Example:
            >>> manager = CitationManager()
            >>> chunk = {
            ...     "text": "AI Engineer path requires Python...",
            ...     "category": "career_path",
            ...     "tags": ["AI", "career"]
            ... }
            >>> citation = manager.create_citation(
            ...     source="Career Database",
            ...     confidence_score=0.92
            ... )
            >>> cited_chunk = manager.attach_citation_to_chunk(chunk, citation)
            >>> # Original fields preserved
            >>> cited_chunk["category"]
            'career_path'
            >>> # Citation added
            >>> cited_chunk["citation"]["source"]
            'Career Database'
        """
        if chunk is None:
            logger.warning("Attempted to cite None chunk")
            return {}
        
        # Create a copy to avoid mutating original
        result = dict(chunk)
        
        # Add citation if provided
        if citation:
            result["citation"] = citation.to_dict()
            logger.debug(f"Citation attached to chunk: {chunk.get('id', 'unknown')}")
        
        return result

    def add_citations_to_chunks(
        self,
        chunks: List[Dict[str, Any]],
        citations: Optional[List[Optional[Citation]]] = None
    ) -> List[Dict[str, Any]]:
        """
        Batch attach citations to multiple chunks.
        
        Handles mismatched lengths gracefully:
        - If citations list is shorter, remaining chunks get no citation
        - If citations list is longer, extras are ignored
        - None values in citations list are skipped
        
        Args:
            chunks: List of knowledge chunk dictionaries
            citations: Optional list of Citation objects (can contain None)
        
        Returns:
            List[Dict]: Enhanced chunks with citations
        
        Example:
            >>> manager = CitationManager()
            >>> chunks = [
            ...     {"text": "Python basics...", "category": "basics"},
            ...     {"text": "ML concepts...", "category": "ml"},
            ...     {"text": "Deployment tips...", "category": "devops"}
            ... ]
            >>> citations = [
            ...     Citation(source="Tutorial Platform", confidence_score=0.85),
            ...     Citation(source="Research Paper", confidence_score=0.95),
            ...     None  # Third chunk won't have citation
            ... ]
            >>> cited_chunks = manager.add_citations_to_chunks(chunks, citations)
            >>> len(cited_chunks)
            3
            >>> "citation" in cited_chunks[0]
            True
            >>> "citation" in cited_chunks[2]
            False
        """
        if not chunks:
            logger.warning("add_citations_to_chunks called with empty chunk list")
            return []
        
        if citations is None:
            citations = []
        
        result = []
        
        for i, chunk in enumerate(chunks):
            # Get corresponding citation if available
            citation = citations[i] if i < len(citations) else None
            
            # Attach citation (None is handled gracefully)
            cited_chunk = self.attach_citation_to_chunk(chunk, citation)
            result.append(cited_chunk)
        
        logger.info(f"Added citations to {len(result)} chunks "
                   f"(applied {sum(1 for c in citations if c)} citations)")
        
        return result

    def get_citation_summary(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics about citations in chunks.
        
        Args:
            chunks: List of chunks (with optional citation fields)
        
        Returns:
            Dict with citation statistics
        
        Example:
            >>> manager = CitationManager()
            >>> chunks = [
            ...     {"text": "...", "citation": {"source": "DB", "confidence_score": 0.9}},
            ...     {"text": "...", "citation": {"source": "API", "confidence_score": 0.85}},
            ...     {"text": "..."}  # No citation
            ... ]
            >>> summary = manager.get_citation_summary(chunks)
            >>> summary["total_chunks"]
            3
            >>> summary["cited_chunks"]
            2
            >>> summary["avg_confidence"]
            0.875
        """
        total_chunks = len(chunks)
        cited_chunks = 0
        confidence_scores = []
        sources = {}
        
        for chunk in chunks:
            if "citation" in chunk and chunk["citation"]:
                cited_chunks += 1
                citation_data = chunk["citation"]
                
                # Track source usage
                source = citation_data.get("source", "Unknown")
                sources[source] = sources.get(source, 0) + 1
                
                # Collect confidence scores
                confidence = citation_data.get("confidence_score")
                if confidence is not None:
                    confidence_scores.append(confidence)
        
        avg_confidence = (
            sum(confidence_scores) / len(confidence_scores)
            if confidence_scores else None
        )
        
        summary = {
            "total_chunks": total_chunks,
            "cited_chunks": cited_chunks,
            "uncited_chunks": total_chunks - cited_chunks,
            "citation_rate": round(cited_chunks / max(total_chunks, 1) * 100, 1),
            "avg_confidence": round(avg_confidence, 3) if avg_confidence else None,
            "sources_used": sources,
            "unique_sources": len(sources)
        }
        
        logger.info(f"Citation summary: {summary['citation_rate']}% cited "
                   f"(avg confidence: {summary.get('avg_confidence', 'N/A')})")
        
        return summary
