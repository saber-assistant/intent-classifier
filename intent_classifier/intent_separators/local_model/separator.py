from ..base import IntentSeparator

class LocalModelIntentSeparator(IntentSeparator):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
    async def create_segments(self, content: str) -> list[str]:
        return [content]