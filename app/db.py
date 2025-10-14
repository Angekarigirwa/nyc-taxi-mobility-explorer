from __future__ import annotations

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from .models import Base


def get_engine(db_url: str):
	engine = create_engine(db_url, future=True)
	return engine


def init_db(engine) -> None:
	Base.metadata.create_all(engine)


def create_session_factory(engine):
	return sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


