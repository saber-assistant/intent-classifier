class IntentLayer:
    """
    Base class for all intent layers.
    """
    def __init__(self, **kwargs):
        pass

    async def check_condition(self, previous_segments: list[str], segment: str, is_partial: bool = False) -> bool:
        """
        Check if the content matches the intent layer.
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")


    async def classify(self, previous_segments: list[str], segment: str, is_partial: bool = False) -> list[dict]:
        """
        Classify the given text and return the result(s).
        Should be implemented by subclasses.
        """
        raise NotImplementedError("Subclasses must implement this method.")
