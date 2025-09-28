from core import settings
from sqlalchemy import URL
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

url_object = URL.create(
    "postgresql+asyncpg",
    username=settings.PG_USER,
    password=settings.PG_PASSWORD,
    host=settings.PG_HOST,
    port=settings.PG_PORT,
    database=settings.PG_DATABASE,
)

engine = create_async_engine(url_object, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


# Dependency
async def get_session():
    async with AsyncSessionLocal() as session:
        yield session
