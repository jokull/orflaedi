import os

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL", "postgresql+asyncpg://orflaedi:@localhost/orflaedi"
)

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={})
session = sessionmaker(
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    bind=engine,
    class_=AsyncSession,
)

Base = declarative_base()
