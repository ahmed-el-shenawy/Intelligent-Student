from helpers import async_session, settings

class BaseModel:
    def __init__(self):
        self.settings = settings
        self.async_session = async_session

    async def get_session(self):
        async with self.async_session() as session:
            yield session
