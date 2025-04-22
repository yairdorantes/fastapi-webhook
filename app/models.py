from sqlalchemy import Column, Integer, String
from database import Base


class Script(Base):
    __tablename__ = "Scripts"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
