"""
CVMatch Database Models
Uses SQLAlchemy for ORM with PostgreSQL
"""

from sqlalchemy import Column, Integer, String, Float, Text, Boolean, DateTime, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id          = Column(Integer, primary_key=True, index=True)
    name        = Column(String(100), nullable=False)
    email       = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255))
    role        = Column(String(50), default="student")  # student | professional | recruiter
    plan        = Column(String(20), default="free")     # free | premium
    avatar_url  = Column(String(500))
    location    = Column(String(100))
    linkedin_url = Column(String(300))
    github_url  = Column(String(300))
    scan_count  = Column(Integer, default=0)
    is_active   = Column(Boolean, default=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    resumes      = relationship("Resume", back_populates="user", cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatMessage", back_populates="user", cascade="all, delete-orphan")
    saved_jobs   = relationship("SavedJob", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User {self.email}>"


class Resume(Base):
    __tablename__ = "resumes"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    file_name    = Column(String(255))
    file_url     = Column(String(500))     # S3 URL
    file_type    = Column(String(10))      # pdf | docx
    raw_text     = Column(Text)
    ats_score    = Column(Integer, default=0)
    kw_score     = Column(Integer, default=0)
    skill_score  = Column(Integer, default=0)
    format_score = Column(Integer, default=0)
    exp_score    = Column(Integer, default=0)
    detected_skills = Column(JSON, default=list)
    strengths    = Column(JSON, default=list)
    weaknesses   = Column(JSON, default=list)
    improvements = Column(JSON, default=list)
    contact_info = Column(JSON, default=dict)
    is_active    = Column(Boolean, default=True)
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user         = relationship("User", back_populates="resumes")
    matches      = relationship("JobMatch", back_populates="resume", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Resume {self.file_name} score={self.ats_score}>"


class Job(Base):
    __tablename__ = "jobs"

    id           = Column(Integer, primary_key=True, index=True)
    title        = Column(String(200), nullable=False, index=True)
    company      = Column(String(200), nullable=False, index=True)
    location     = Column(String(200))
    job_type     = Column(String(50))      # full-time | internship | contract
    source       = Column(String(50))      # linkedin | naukri | internshala | indeed | wellfound
    source_url   = Column(String(500))
    salary_min   = Column(Integer)
    salary_max   = Column(Integer)
    salary_display = Column(String(100))
    description  = Column(Text)
    requirements = Column(JSON, default=list)
    skills       = Column(JSON, default=list)
    exp_required = Column(Integer, default=0)
    education    = Column(String(200))
    tags         = Column(JSON, default=list)
    is_active    = Column(Boolean, default=True)
    posted_at    = Column(DateTime)
    expires_at   = Column(DateTime)
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    matches      = relationship("JobMatch", back_populates="job", cascade="all, delete-orphan")
    saved_by     = relationship("SavedJob", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Job {self.title} @ {self.company}>"


class JobMatch(Base):
    __tablename__ = "job_matches"

    id              = Column(Integer, primary_key=True, index=True)
    resume_id       = Column(Integer, ForeignKey("resumes.id"), nullable=False)
    job_id          = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    match_score     = Column(Float, default=0.0)
    matched_skills  = Column(JSON, default=list)
    missing_skills  = Column(JSON, default=list)
    recommendation  = Column(String(200))
    created_at      = Column(DateTime, default=datetime.utcnow)

    # Relationships
    resume = relationship("Resume", back_populates="matches")
    job    = relationship("Job", back_populates="matches")

    def __repr__(self):
        return f"<JobMatch resume={self.resume_id} job={self.job_id} score={self.match_score}>"


class Application(Base):
    __tablename__ = "applications"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id      = Column(Integer, nullable=False)
    job_title   = Column(String(200))
    company     = Column(String(200))
    status      = Column(String(50), default="applied")  # applied | screening | interview | offered | rejected
    match_score = Column(Integer, default=0)
    notes       = Column(Text)
    applied_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="applications")

    def __repr__(self):
        return f"<Application {self.job_title} @ {self.company} status={self.status}>"


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id           = Column(Integer, primary_key=True, index=True)
    user_id      = Column(Integer, ForeignKey("users.id"), nullable=False)
    session_id   = Column(String(100))
    role         = Column(String(20))   # user | assistant
    content      = Column(Text, nullable=False)
    tokens_used  = Column(Integer, default=0)
    model_used   = Column(String(100))
    created_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="chat_history")

    def __repr__(self):
        return f"<ChatMessage user={self.user_id} role={self.role}>"


class SavedJob(Base):
    __tablename__ = "saved_jobs"

    id         = Column(Integer, primary_key=True, index=True)
    user_id    = Column(Integer, ForeignKey("users.id"), nullable=False)
    job_id     = Column(Integer, ForeignKey("jobs.id"), nullable=False)
    saved_at   = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="saved_jobs")
    job  = relationship("Job", back_populates="saved_by")

    def __repr__(self):
        return f"<SavedJob user={self.user_id} job={self.job_id}>"


class SkillRoadmap(Base):
    __tablename__ = "skill_roadmaps"

    id          = Column(Integer, primary_key=True, index=True)
    user_id     = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_role = Column(String(200))
    current_skills = Column(JSON, default=list)
    gap_skills  = Column(JSON, default=list)
    roadmap     = Column(JSON, default=dict)   # week-by-week plan
    created_at  = Column(DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<SkillRoadmap user={self.user_id} role={self.target_role}>"
