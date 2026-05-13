
import os 
from sqlalchemy.ext.asyncio import create_async_engine,async_sessionmaker
from sqlalchemy.orm import DeclarativeBase 

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./test.db"
)
engine = create_async_engine(
    DATABASE_URL,
    connect_args={"check_same_thread":False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = async_sessionmaker(
    engine,
    expire_on_commit=False
)


class Base(DeclarativeBase):
    pass

async def get_db():
    async with SessionLocal() as db:
        yield db

async def init_db():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.drop_all)
        await connection.run_sync(Base.metadata.create_all)
