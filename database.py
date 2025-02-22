from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    app = Column(String(50), nullable=False)
    version = Column(String(50), nullable=False)
    event_type = Column(String(20), nullable=False)
    client_ip = Column(String(50), nullable=False)
    created_at = Column(DateTime, default=func.now())

class Authorization(Base):
    __tablename__ = "authorizations"

    id = Column(Integer, primary_key=True, index=True)
    app = Column(String(50), nullable=False)
    version_rule = Column(String(50), nullable=False)
    ip_rule = Column(Text, nullable=False)
    detail_info = Column(Text, nullable=False)
    created_at = Column(DateTime, default=func.now())

# 创建数据库表
Base.metadata.create_all(bind=engine)

# 依赖项
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
