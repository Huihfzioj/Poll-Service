from sqlalchemy import Column, ForeignKey, Integer, String, create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, relationship

DATABASE_URL = "sqlite:///./polls.db"
engine = create_engine( DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind = engine)
Base = declarative_base()

#----------- Models -----------------
class Poll(Base) : 
    __tablename__ = "polls"
    id = Column(Integer, primary_key=True)
    question = Column(String, nullable=False)
    options = relationship("Option", cascade="all, delete")
class Option(Base) :
    __tablename__ = "options"
    id = Column(Integer, primary_key=True)
    text = Column(String, nullable=False)
    votes = Column(Integer, default=0)
    poll_id = Column(Integer, ForeignKey("polls.id"))

# Create tables
Base.metadata.create_all(bind=engine)