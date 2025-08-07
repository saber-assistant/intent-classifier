class IntentLayer:
    """
    Base class for all intent layers.
    """
    def __init__(self, **kwargs):
        pass
    
    async def matches_content(self, content: str) -> bool:
        """
        Check if the content matches the intent layer.
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")

    async def classify(self, text: str) -> list[dict]:
        """
        Classify the given text and return the result(s).
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
