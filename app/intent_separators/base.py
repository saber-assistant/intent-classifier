from typing import List


class IntentSeparator:
    """
    Abstract base class for identifying and separating segments in text content
    that may contain multiple intents or require separate classification.
    
    Intent separators are responsible for taking raw input text and breaking it
    into logical segments that can be independently classified by intent layers.
    """
    
    def __init__(self, **kwargs):
        """
        Initialize the intent separator with configuration options.
        
        Args:
            **kwargs: Configuration parameters specific to the separator implementation
        """
        self.kwargs = kwargs
    
    
    async def check_condition(self, content: str) -> bool:
        """
        Determine if the given content needs to be segmented based on certain keywords.
        
        This method can be used for optimization - if content doesn't need
        segmentation, it can skip the more expensive get_segments() operation.
        """
        raise NotImplementedError(
            "check_condition() must be implemented by subclasses"
        )


    async def should_segment(self, content: str) -> bool:
        """
        Determine if the given content needs to be segmented based on certain keywords.
        
        This method can be used for optimization - if content doesn't need
        segmentation, it can skip the more expensive get_segments() operation.
        
        Args:
            content: The raw text content to analyze
            
        Returns:
            True if the content should be segmented, False otherwise
        """
        raise NotImplementedError(
            "should_segment() must be implemented by subclasses"
        )
        
        
    async def get_segments(self, content: str) -> List[str]:
        """
        Split the given content into segments that can be independently classified.
        
        Args:
            content: The raw text content to be segmented
            
        Returns:
            List of text segments, each representing a potential independent intent.
            If no segmentation is needed, returns a list with the original content.
            
        Raises:
            ValueError: If the content cannot be processed
            
        Examples:
            >>> separator = SomeSeparator()
            >>> await separator.get_segments("Hello. How are you? Goodbye!")
            ["Hello.", "How are you?", "Goodbye!"]
        """
        raise NotImplementedError(
            "get_segments() must be implemented by subclasses"
        )
    


    async def _validate_segment(self, segment: str) -> bool:
        """
        Validate that the generated segments are reasonable.
        
        This can be used to ensure segments meet certain criteria
        (e.g., minimum length, not empty, etc.)
        
        Args:
            segment: The segment to validate

        Returns:
            True if the segment is valid, False otherwise
        """
        # Default validation: ensure no empty segments and reasonable length
        s = segment.strip()
        return s and len(s) > 3


    async def _build_segment(self, _type: str, text: str, metadata: dict = {}) -> str:
        """
        Segment types:
        - "text": Regular text segment
        """
        return {
            "type": _type,
            "text": text,
            "metadata": metadata
        }
