from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship
from .db import Base
import datetime

class Conversation(Base):
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String, nullable=False, default="anonymous_user")
    start_time = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)
    end_time = Column(DateTime(timezone=True), nullable=True)

    logs = relationship("AgentLog", back_populates="conversation")

class AgentLog(Base):
    __tablename__ = "agent_logs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    agent_name = Column(String, nullable=False)
    user_query = Column(Text, nullable=True)
    agent_response = Column(Text, nullable=True)
    tool_used = Column(String, nullable=True)
    outcome = Column(Text, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=datetime.datetime.utcnow)

    conversation = relationship("Conversation", back_populates="logs")