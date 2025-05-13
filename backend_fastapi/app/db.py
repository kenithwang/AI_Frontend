from sqlalchemy import create_engine, Column, String, Text, DateTime, Integer, Float, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# 数据库连接信息（请根据实际情况修改）
DATABASE_URL = os.getenv('AUDIO_TASKS_DB_URL', 'postgresql+psycopg2://postgres:postgres@localhost:5432/audio_tasks')
engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Task(Base):
    __tablename__ = 'tasks'
    task_id = Column(String, primary_key=True, index=True)
    submit_time = Column(DateTime)
    finish_time = Column(DateTime, nullable=True)
    status = Column(String)
    to_email = Column(String)
    cc_emails = Column(Text)
    submitter_ip = Column(String)
    user_agent = Column(Text)
    user_id = Column(String)
    file_name = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    file_type = Column(String)
    audio_duration = Column(Float)
    model = Column(String)
    output_type = Column(String)
    extra_options = Column(JSON, nullable=True)
    log = Column(Text)
    error = Column(Text)
    result_files = Column(JSON, nullable=True)
    processing_time = Column(Float)
    email_sent = Column(Boolean)
    email_status = Column(Text)
    user_feedback = Column(Text)
    last_update_time = Column(DateTime)
    operator = Column(String)

# 初始化建表
if __name__ == "__main__":
    Base.metadata.create_all(bind=engine) 