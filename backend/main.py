"""
CVMatch Backend – FastAPI Application
Full-stack AI Resume Analysis & Job Matching Platform
"""

from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
import re
import json
import random
import hashlib
from datetime import datetime

app = FastAPI(
    title="CVMatch API",
    description="AI-powered resume analysis and job matching platform",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS – allow frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ──────────────────────────────────────────────
# Pydantic Models
# ──────────────────────────────────────────────

class JobMatchRequest(BaseModel):
    resume_text: str
    job_description: str

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[dict]] = []
    user_profile: Optional[dict] = {}

class ResumeImproveRequest(BaseModel):
    resume_text: str
    target_role: Optional[str] = ""
    job_description: Optional[str] = ""

class JobSearchRequest(BaseModel):
    skills: List[str]
    experience_years: Optional[int] = 0
    location: Optional[str] = "Remote"
    job_type: Optional[str] = "all"  # all | job | internship

class UserRegister(BaseModel):
    name: str
    email: str
    password: str
    role: Optional[str] = "student"

class ATSRequest(BaseModel):
    resume_text: str


# ──────────────────────────────────────────────
# In-Memory Stores (replace with PostgreSQL)
# ──────────────────────────────────────────────

USERS_DB = {}
RESUMES_DB = {}
ANALYSES_DB = {}


# ──────────────────────────────────────────────
# Skills Database
# ──────────────────────────────────────────────

TECH_SKILLS = [
    "Python", "Java", "JavaScript", "TypeScript", "C++", "C", "Go", "Rust", "Kotlin", "Swift",
    "React", "React.js", "Angular", "Vue.js", "Next.js", "Node.js", "Express.js", "Django",
    "FastAPI", "Flask", "Spring Boot", "Laravel", "Ruby on Rails",
    "Machine Learning", "Deep Learning", "Natural Language Processing", "Computer Vision",
    "TensorFlow", "PyTorch", "Scikit-learn", "Keras", "OpenCV", "HuggingFace",
    "SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis", "Cassandra", "Elasticsearch",
    "AWS", "GCP", "Azure", "Docker", "Kubernetes", "Terraform", "CI/CD", "DevOps",
    "Git", "GitHub", "GitLab", "REST API", "GraphQL", "Microservices",
    "Data Analysis", "Pandas", "NumPy", "Matplotlib", "Seaborn", "Tableau", "Power BI",
    "Apache Spark", "Kafka", "Hadoop", "Airflow", "dbt",
    "HTML", "CSS", "Tailwind CSS", "Bootstrap", "SASS",
    "Linux", "Bash", "Shell Scripting", "Agile", "Scrum",
    "LangChain", "OpenAI", "Claude API", "RAG", "Vector Databases", "Pinecone", "ChromaDB",
]

SOFT_SKILLS = [
    "Problem Solving", "Team Collaboration", "Communication", "Leadership",
    "Project Management", "Critical Thinking", "Time Management",
]


# ──────────────────────────────────────────────
# Helper Functions
# ──────────────────────────────────────────────

def extract_skills_from_text(text: str) -> List[str]:
    """Extract known skills from resume/JD text."""
    text_lower = text.lower()
    found = []
    for skill in TECH_SKILLS + SOFT_SKILLS:
        pattern = r'\b' + re.escape(skill.lower()) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(dict.fromkeys(found))  # preserve order, deduplicate


def extract_contact_info(text: str) -> dict:
    """Extract name, email, phone from resume text."""
    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    phone_pattern = r'(\+91[-\s]?)?[6-9]\d{9}'

    emails = re.findall(email_pattern, text)
    phones = re.findall(phone_pattern, text)

    lines = [l.strip() for l in text.split('\n') if l.strip()]
    name = lines[0] if lines else "Unknown"

    return {
        "name": name,
        "email": emails[0] if emails else None,
        "phone": phones[0] if phones else None,
    }


def calculate_ats_score(resume_text: str, job_description: str = "") -> dict:
    """
    Calculate ATS score based on:
    - Keyword density (40%)
    - Section completeness (25%)
    - Formatting quality (20%)
    - Experience relevance (15%)
    """
    text_lower = resume_text.lower()
    score_breakdown = {}

    # 1. KEYWORD SCORE (40 pts)
    resume_skills = extract_skills_from_text(resume_text)
    keyword_score = min(40, len(resume_skills) * 2.5)
    score_breakdown["keywords"] = round(keyword_score)

    # 2. SECTIONS SCORE (25 pts)
    sections = {
        "experience": any(w in text_lower for w in ["experience", "work history", "employment"]),
        "education": any(w in text_lower for w in ["education", "b.tech", "bachelor", "master", "degree", "university", "college"]),
        "skills": any(w in text_lower for w in ["skills", "technical skills", "proficiencies"]),
        "projects": any(w in text_lower for w in ["project", "built", "developed", "created"]),
        "summary": any(w in text_lower for w in ["summary", "objective", "about", "profile"]),
        "contact": any(w in text_lower for w in ["email", "phone", "linkedin", "github"]),
    }
    section_score = sum(1 for v in sections.values() if v) / len(sections) * 25
    score_breakdown["sections"] = round(section_score)

    # 3. FORMATTING SCORE (20 pts)
    # Check for bullet points, consistent structure
    bullet_count = text_lower.count('•') + text_lower.count('-') + text_lower.count('*')
    has_numbers = bool(re.search(r'\d+%|\d+\+|\$\d+|₹\d+', resume_text))
    formatting_score = min(20, (bullet_count * 0.5) + (10 if has_numbers else 0))
    score_breakdown["formatting"] = round(formatting_score)

    # 4. EXPERIENCE RELEVANCE (15 pts)
    exp_indicators = ["year", "month", "intern", "engineer", "analyst", "developer", "manager", "led", "managed", "built", "developed"]
    exp_matches = sum(1 for w in exp_indicators if w in text_lower)
    exp_score = min(15, exp_matches * 1.2)
    score_breakdown["experience"] = round(exp_score)

    # Total raw score
    raw_total = sum(score_breakdown.values())

    # Scale to 0-100 with some randomness for demo realism
    total = min(97, max(40, raw_total + random.randint(-3, 5)))

    # JD Match bonus
    jd_match_score = 0
    if job_description:
        jd_skills = extract_skills_from_text(job_description)
        matched = [s for s in resume_skills if s in jd_skills]
        missing = [s for s in jd_skills if s not in resume_skills]
        jd_match_score = round(len(matched) / max(len(jd_skills), 1) * 100)
    else:
        matched, missing = [], []

    # Percentage sub-scores
    sub_scores = {
        "keywords": round(score_breakdown["keywords"] / 40 * 100),
        "sections": round(score_breakdown["sections"] / 25 * 100),
        "formatting": round(score_breakdown["formatting"] / 20 * 100),
        "experience": round(score_breakdown["experience"] / 15 * 100),
    }

    return {
        "total_score": total,
        "sub_scores": sub_scores,
        "jd_match_score": jd_match_score,
        "matched_skills": matched,
        "missing_skills": missing,
        "detected_skills": resume_skills,
        "sections_found": sections,
    }


def generate_improvements(score_data: dict, resume_text: str) -> List[dict]:
    """Generate prioritized improvement suggestions."""
    improvements = []
    text_lower = resume_text.lower()
    ss = score_data["sub_scores"]

    if ss["sections"] < 80:
        if "summary" not in text_lower and "objective" not in text_lower:
            improvements.append({
                "priority": "high",
                "category": "Content",
                "title": "Add a Professional Summary",
                "description": "Add a 2-3 sentence summary at the top. This is the first thing recruiters read and significantly impacts ATS scoring.",
                "impact": "+8-12 ATS points"
            })

    if len(score_data["detected_skills"]) < 8:
        improvements.append({
            "priority": "high",
            "category": "Skills",
            "title": "Expand Your Skills Section",
            "description": "Add a dedicated Technical Skills section with categorized tools (Languages, Frameworks, Databases, Cloud, etc.)",
            "impact": "+10-15 ATS points"
        })

    if ss["formatting"] < 75:
        improvements.append({
            "priority": "medium",
            "category": "Formatting",
            "title": "Add Quantifiable Achievements",
            "description": "Replace vague descriptions with metrics: '40% faster', 'served 10K users', 'reduced bugs by 60%'. Numbers get noticed.",
            "impact": "+6-10 ATS points"
        })

    if "certif" not in text_lower:
        improvements.append({
            "priority": "medium",
            "category": "Credentials",
            "title": "Add Certifications",
            "description": "Include relevant certifications (AWS, Google Cloud, Coursera, HackerRank). Even free certificates improve ATS performance.",
            "impact": "+5-8 ATS points"
        })

    if "github" not in text_lower and "linkedin" not in text_lower:
        improvements.append({
            "priority": "low",
            "category": "Contact",
            "title": "Add GitHub & LinkedIn URLs",
            "description": "Include clickable profile links. Recruiters expect these — especially for tech roles.",
            "impact": "+3-5 ATS points"
        })

    if score_data["missing_skills"]:
        top_missing = score_data["missing_skills"][:3]
        improvements.append({
            "priority": "high",
            "category": "Skills Gap",
            "title": f"Add Missing Skills: {', '.join(top_missing)}",
            "description": f"The job requires {', '.join(top_missing)} which aren't in your resume. Learn and add them to boost your match score significantly.",
            "impact": f"+{len(top_missing) * 5}% match score"
        })

    return improvements[:6]


def get_resume_strengths_weaknesses(text: str, score_data: dict) -> dict:
    """Generate strengths and weaknesses based on analysis."""
    text_lower = text.lower()
    strengths = []
    weaknesses = []

    if len(score_data["detected_skills"]) >= 8:
        strengths.append("Strong technical skills section")
    if score_data["sub_scores"]["formatting"] >= 80:
        strengths.append("Good resume formatting — ATS-friendly")
    if re.search(r'\d+%|\d+\s*users|\$\d+|₹\d+', text):
        strengths.append("Quantified achievements with metrics")
    if "project" in text_lower:
        strengths.append("Solid project experience demonstrated")
    if any(w in text_lower for w in ["b.tech", "engineering", "computer science"]):
        strengths.append("Relevant educational background")

    if "summary" not in text_lower and "objective" not in text_lower:
        weaknesses.append("Missing professional summary section")
    if "certif" not in text_lower:
        weaknesses.append("No certifications listed")
    if score_data["sub_scores"]["experience"] < 70:
        weaknesses.append("Experience section needs more detail")
    if score_data["missing_skills"]:
        weaknesses.append(f"Missing in-demand skills: {', '.join(score_data['missing_skills'][:2])}")
    if "github" not in text_lower:
        weaknesses.append("GitHub profile URL not included")

    return {
        "strengths": strengths[:4],
        "weaknesses": weaknesses[:4]
    }


# ──────────────────────────────────────────────
# Demo Job Data (replace with real scrapers)
# ──────────────────────────────────────────────

DEMO_JOBS = [
    {"id": 1, "title": "Software Engineer", "company": "Google", "location": "Bangalore / Remote", "type": "full-time", "source": "linkedin", "salary": "₹18-25 LPA", "skills": ["Python", "Java", "Algorithms", "System Design", "SQL"], "exp_required": 0, "url": "https://careers.google.com"},
    {"id": 2, "title": "Data Analyst Intern", "company": "Razorpay", "location": "Bangalore (Hybrid)", "type": "internship", "source": "internshala", "salary": "₹25,000/month", "skills": ["Python", "SQL", "Excel", "Data Analysis", "Statistics"], "exp_required": 0, "url": "https://internshala.com"},
    {"id": 3, "title": "ML Engineer", "company": "Flipkart", "location": "Bangalore", "type": "full-time", "source": "naukri", "salary": "₹15-20 LPA", "skills": ["Python", "TensorFlow", "Machine Learning", "Pandas", "AWS"], "exp_required": 0, "url": "https://naukri.com"},
    {"id": 4, "title": "Frontend Developer Intern", "company": "CRED", "location": "Remote", "type": "internship", "source": "wellfound", "salary": "₹20,000/month", "skills": ["React.js", "JavaScript", "CSS", "HTML", "Git"], "exp_required": 0, "url": "https://wellfound.com"},
    {"id": 5, "title": "Data Science Engineer", "company": "Swiggy", "location": "Bangalore", "type": "full-time", "source": "linkedin", "salary": "₹12-18 LPA", "skills": ["Python", "Machine Learning", "SQL", "Data Analysis", "REST API"], "exp_required": 1, "url": "https://linkedin.com/jobs"},
    {"id": 6, "title": "Python Backend Developer", "company": "Zerodha", "location": "Bangalore", "type": "full-time", "source": "naukri", "salary": "₹10-15 LPA", "skills": ["Python", "FastAPI", "PostgreSQL", "REST API", "Git"], "exp_required": 0, "url": "https://naukri.com"},
    {"id": 7, "title": "AI Research Intern", "company": "Microsoft India", "location": "Hyderabad (Hybrid)", "type": "internship", "source": "linkedin", "salary": "₹60,000/month", "skills": ["Python", "Machine Learning", "Deep Learning", "PyTorch"], "exp_required": 0, "url": "https://linkedin.com/jobs"},
    {"id": 8, "title": "Full Stack Developer", "company": "Josh Technology", "location": "Gurgaon / Remote", "type": "full-time", "source": "indeed", "salary": "₹8-12 LPA", "skills": ["React.js", "Node.js", "MongoDB", "REST API", "JavaScript"], "exp_required": 0, "url": "https://indeed.com"},
    {"id": 9, "title": "Data Analytics Intern", "company": "Internshala", "location": "Remote", "type": "internship", "source": "internshala", "salary": "₹10,000/month", "skills": ["Python", "SQL", "Excel", "Data Analysis"], "exp_required": 0, "url": "https://internshala.com"},
    {"id": 10, "title": "DevOps Engineer", "company": "PhonePe", "location": "Bangalore", "type": "full-time", "source": "linkedin", "salary": "₹12-18 LPA", "skills": ["Docker", "Kubernetes", "AWS", "CI/CD", "Python", "Linux"], "exp_required": 1, "url": "https://linkedin.com/jobs"},
]


def calculate_job_match(user_skills: List[str], job: dict) -> dict:
    """Calculate match % between user skills and job requirements."""
    job_skills = job["skills"]
    user_skill_lower = [s.lower() for s in user_skills]
    job_skill_lower = [s.lower() for s in job_skills]

    matched = [s for s in job_skills if s.lower() in user_skill_lower]
    missing = [s for s in job_skills if s.lower() not in user_skill_lower]

    if not job_skills:
        match_pct = 50
    else:
        match_pct = round(len(matched) / len(job_skills) * 100)
        # Add some variance for realism
        match_pct = min(97, max(30, match_pct + random.randint(-3, 8)))

    return {
        **job,
        "match_score": match_pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "chance_of_selection": f"{match_pct}%",
    }


# ──────────────────────────────────────────────
# API Routes
# ──────────────────────────────────────────────

@app.get("/")
def root():
    return {
        "message": "CVMatch API is running 🚀",
        "version": "1.0.0",
        "docs": "/api/docs"
    }


@app.get("/api/health")
def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}


# ── AUTH ──────────────────────────────────────

@app.post("/api/auth/register")
def register(user: UserRegister):
    if user.email in USERS_DB:
        raise HTTPException(status_code=400, detail="Email already registered")

    user_id = hashlib.md5(user.email.encode()).hexdigest()[:8]
    USERS_DB[user.email] = {
        "id": user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role,
        "created_at": datetime.utcnow().isoformat(),
        "plan": "free",
        "scan_count": 0,
    }
    return {
        "success": True,
        "user_id": user_id,
        "name": user.name,
        "token": f"cvmatch_token_{user_id}",
        "message": "Account created successfully"
    }


@app.post("/api/auth/login")
def login(email: str, password: str):
    if email not in USERS_DB:
        # For demo: create user on first login
        user_id = hashlib.md5(email.encode()).hexdigest()[:8]
        USERS_DB[email] = {
            "id": user_id, "name": "Demo User", "email": email,
            "role": "student", "plan": "free", "scan_count": 0
        }
    user = USERS_DB[email]
    return {
        "success": True,
        "token": f"cvmatch_token_{user['id']}",
        "user": {k: v for k, v in user.items() if k != "password"}
    }


# ── RESUME ANALYSIS ───────────────────────────

@app.post("/api/resume/analyze")
async def analyze_resume(file: UploadFile = File(...)):
    """Upload and analyze a resume file (PDF/DOCX)."""
    if file.content_type not in ["application/pdf", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "text/plain"]:
        raise HTTPException(status_code=400, detail="Only PDF, DOCX, or TXT files are supported")

    content = await file.read()

    # For demo: simulate text extraction
    # In production: use pdfplumber for PDF, python-docx for DOCX
    sample_resume_text = """
    Priya Sharma
    priya.sharma@email.com | +91 9876543210 | linkedin.com/in/priya | github.com/priya-sharma

    EDUCATION
    B.Tech in Information Technology | Lovely Professional University | 2021-2025 | CGPA: 8.2

    SKILLS
    Languages: Python, JavaScript, Java, SQL
    Frameworks: React.js, FastAPI, TensorFlow, Pandas, NumPy
    Tools: Git, Docker, AWS, Postman, Jupyter Notebook
    Databases: PostgreSQL, MongoDB

    EXPERIENCE
    Data Science Intern | ABC Analytics | June 2024 - August 2024
    - Built ML models using Python and Scikit-learn, improving forecast accuracy by 18%
    - Analyzed 100K+ customer records using Pandas and SQL to identify churn patterns
    - Created interactive dashboards using Matplotlib and Streamlit

    PROJECTS
    AI Recommendation Engine
    - Developed a collaborative filtering system using TensorFlow serving 50K+ users
    - Deployed on AWS with 99.9% uptime, reduced recommendation latency by 40%

    Student Attendance System
    - Built full-stack app using React.js + FastAPI + PostgreSQL
    - Automated attendance tracking for 2000+ students, reducing manual work by 80%

    CERTIFICATIONS
    - Python for Data Science – Coursera (2024)
    - AWS Cloud Practitioner – AWS (2024)
    """

    score_data = calculate_ats_score(sample_resume_text)
    sw = get_resume_strengths_weaknesses(sample_resume_text, score_data)
    improvements = generate_improvements(score_data, sample_resume_text)
    contact = extract_contact_info(sample_resume_text)

    result = {
        "success": True,
        "file_name": file.filename,
        "contact_info": contact,
        "ats_score": score_data["total_score"],
        "sub_scores": {
            "keywords": score_data["sub_scores"]["keywords"],
            "skills": score_data["sub_scores"]["sections"],
            "formatting": score_data["sub_scores"]["formatting"],
            "experience": score_data["sub_scores"]["experience"],
        },
        "detected_skills": score_data["detected_skills"],
        "strengths": sw["strengths"],
        "weaknesses": sw["weaknesses"],
        "improvements": improvements,
        "sections_found": score_data["sections_found"],
        "resume_text_preview": sample_resume_text[:300] + "...",
        "analyzed_at": datetime.utcnow().isoformat(),
    }

    # Store in memory
    analysis_id = hashlib.md5(file.filename.encode()).hexdigest()[:8]
    ANALYSES_DB[analysis_id] = result

    return {**result, "analysis_id": analysis_id}


@app.post("/api/resume/ats-score")
def get_ats_score(request: ATSRequest):
    """Calculate ATS score from raw resume text."""
    score_data = calculate_ats_score(request.resume_text)
    sw = get_resume_strengths_weaknesses(request.resume_text, score_data)
    improvements = generate_improvements(score_data, request.resume_text)

    return {
        "success": True,
        "ats_score": score_data["total_score"],
        "sub_scores": score_data["sub_scores"],
        "detected_skills": score_data["detected_skills"],
        "strengths": sw["strengths"],
        "weaknesses": sw["weaknesses"],
        "improvements": improvements,
    }


@app.post("/api/resume/match-job")
def match_with_job(request: JobMatchRequest):
    """Match resume against a specific job description."""
    resume_skills = extract_skills_from_text(request.resume_text)
    jd_skills = extract_skills_from_text(request.job_description)

    matched = [s for s in jd_skills if s in resume_skills]
    missing = [s for s in jd_skills if s not in resume_skills]

    match_pct = round(len(matched) / max(len(jd_skills), 1) * 100)
    match_pct = min(97, max(25, match_pct + random.randint(-2, 5)))

    # Generate a rewrite example
    before_example = "Worked on machine learning project."
    after_example = "Developed an ML-based recommendation engine using Python & TensorFlow, improving prediction accuracy by 23% and serving 50K+ daily active users."

    return {
        "success": True,
        "match_score": match_pct,
        "matched_skills": matched,
        "missing_skills": missing,
        "resume_skills": resume_skills,
        "jd_skills": jd_skills,
        "selection_probability": f"{match_pct}%",
        "rewrite_example": {
            "before": before_example,
            "after": after_example,
        },
        "recommendation": (
            "Excellent match! Apply immediately and tailor your cover letter." if match_pct >= 85
            else "Good match. Fill the skill gaps and apply with a targeted resume." if match_pct >= 65
            else "Partial match. Focus on upskilling before applying."
        )
    }


@app.post("/api/resume/improve")
def improve_resume(request: ResumeImproveRequest):
    """Generate AI improvement suggestions for resume sections."""
    skills = extract_skills_from_text(request.resume_text)

    rewrites = [
        {
            "section": "Experience Bullet Point",
            "before": "Worked on data analysis project.",
            "after": f"Analyzed 500K+ customer records using Python & Pandas, identifying key churn patterns that reduced customer loss by 18% QoQ.",
        },
        {
            "section": "Professional Summary",
            "before": "Fresher looking for opportunities in software development.",
            "after": f"Results-driven B.Tech IT student with hands-on experience in {', '.join(skills[:3])}. Passionate about building scalable AI solutions. Seeking challenging SDE roles to leverage strong project experience.",
        },
        {
            "section": "Project Description",
            "before": "Made a recommendation system.",
            "after": "Engineered a collaborative filtering recommendation system using TensorFlow, deployed on AWS EC2, achieving 94% user satisfaction across 50K+ active users with <200ms response latency.",
        },
    ]

    return {
        "success": True,
        "target_role": request.target_role or "Software Engineer",
        "rewritten_sections": rewrites,
        "ats_tips": [
            "Use exact keywords from job descriptions",
            "Start each bullet with a strong action verb",
            "Include 2-3 quantified results per role",
            "Keep to 1 page for < 3 years experience",
            "Use a clean, ATS-parseable template",
        ]
    }


# ── JOB RECOMMENDATIONS ───────────────────────

@app.post("/api/jobs/recommend")
def recommend_jobs(request: JobSearchRequest):
    """Recommend jobs based on user skills and preferences."""
    results = []

    for job in DEMO_JOBS:
        # Filter by type
        if request.job_type != "all":
            if request.job_type == "internship" and job["type"] != "internship":
                continue
            if request.job_type == "job" and job["type"] != "full-time":
                continue

        # Filter by experience
        if request.experience_years < job.get("exp_required", 0):
            continue

        match = calculate_job_match(request.skills, job)
        if match["match_score"] >= 20:  # only show decent matches
            results.append(match)

    # Sort by match score
    results.sort(key=lambda x: x["match_score"], reverse=True)

    return {
        "success": True,
        "total": len(results),
        "jobs": results,
        "sources": ["LinkedIn", "Internshala", "Naukri", "Indeed", "Wellfound"],
        "last_updated": datetime.utcnow().isoformat(),
    }


@app.get("/api/jobs/search")
def search_jobs(
    query: str = "",
    job_type: str = "all",
    location: str = "",
    min_match: int = 0,
    source: str = "",
):
    """Search jobs with filters."""
    results = DEMO_JOBS

    if query:
        q = query.lower()
        results = [j for j in results if q in j["title"].lower() or q in j["company"].lower()]

    if job_type != "all":
        results = [j for j in results if j["type"] == job_type]

    if source:
        results = [j for j in results if j["source"] == source]

    # Add mock match scores
    results = [{**j, "match_score": random.randint(70, 95)} for j in results]

    return {
        "success": True,
        "total": len(results),
        "jobs": results,
    }


@app.get("/api/jobs/{job_id}")
def get_job_detail(job_id: int):
    """Get full details for a specific job."""
    job = next((j for j in DEMO_JOBS if j["id"] == job_id), None)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"success": True, "job": job}


# ── AI CHATBOT ────────────────────────────────

@app.post("/api/chat")
async def chat_endpoint(request: ChatRequest):
    """
    AI Career Assistant endpoint.
    In production: proxies to Claude API.
    Here: returns smart rule-based responses.
    """
    message = request.message.lower()

    # Smart response engine
    if any(w in message for w in ["resume", "cv", "ats"]):
        response = """**Resume Optimization Tips for Better ATS Scores:**

**Quick wins:**
- Add a 2-3 sentence professional summary at the top
- Include exact keywords from the target job description
- Quantify all achievements (%, numbers, impact)
- Use standard section headings (Experience, Education, Skills, Projects)

**ATS Must-Knows:**
- Use simple, single-column layouts — ATS parsers hate tables and columns
- Include both acronyms and full forms: "ML (Machine Learning)"
- Save as PDF unless the employer specifically asks for DOCX
- File size under 5MB

Your current ATS score is **82/100**. Want me to identify the top 3 changes that would push it past 90?"""

    elif any(w in message for w in ["interview", "prepare", "question"]):
        response = """**Interview Preparation Framework:**

**Technical Round Prep:**
- **DSA:** Practice 2-3 problems daily on LeetCode (Easy → Medium → Hard)
- **System Design:** Study concepts like load balancing, caching, databases, APIs
- **Core CS:** OS, DBMS, Networks, OOP — these come up 80% of the time

**Common Interview Pattern (Indian IT):**
1. Introduction (2 min) — prepare this perfectly
2. Technical questions (30-40 min)
3. Project deep-dive — know your projects inside out
4. HR round — salary, relocation, team fit

**Company-Specific:**
- **TCS/Infosys:** Focus on aptitude + basic coding
- **Product companies (Google, Flipkart):** Heavy DSA + system design
- **Startups (Razorpay, CRED):** Problem-solving + cultural fit

Would you like me to run a mock interview session with you for a specific company?"""

    elif any(w in message for w in ["skill", "learn", "roadmap", "course"]):
        response = """**2025 Skill Roadmap — Indian Tech Market:**

**🔥 Highest-Demand Skills Right Now:**
1. **LLM Engineering** (LangChain, RAG, fine-tuning) — ₹15-30 LPA
2. **Cloud + DevOps** (AWS, Docker, Kubernetes) — ₹12-25 LPA
3. **Data Engineering** (Spark, Airflow, dbt) — ₹10-20 LPA
4. **Full Stack (React + Node/Python)** — ₹8-18 LPA

**Your Learning Path (based on your profile):**

Month 1-2: Strengthen Python fundamentals + SQL
Month 3-4: Build 2 ML/AI projects for GitHub
Month 5-6: Add cloud deployment (AWS free tier)
Month 7+: Specialize in LLM/GenAI tools

**Free Certifications that Recruiters Notice:**
- Google Data Analytics (Coursera) — free to audit
- AWS Cloud Practitioner — $100 but worth it
- HackerRank Python/SQL certifications

Which track interests you most? I'll create a detailed week-by-week plan."""

    elif any(w in message for w in ["job", "apply", "company", "salary"]):
        response = """**Job Search Strategy — India 2025:**

**Where to Apply:**
- **LinkedIn:** Best for product companies and MNCs
- **Naukri:** Best for service companies (TCS, Infosys, Wipro)
- **Internshala:** Best for internships and fresher roles
- **Wellfound (AngelList):** Best for startups with ESOPs
- **Company websites directly:** Often faster response

**Application Tips:**
- Apply within 24-48 hours of job posting (recency matters!)
- Tailor your resume for each application (takes 10 min, 3x more callbacks)
- Aim for 85%+ ATS match score before applying
- Follow up after 1 week via LinkedIn

**Your Top Matches Right Now:**
- Software Engineer @ Google — **94% match** — ₹18-25 LPA
- Data Analyst Intern @ Razorpay — **91% match** — ₹25K/month
- ML Engineer @ Flipkart — **88% match** — ₹15-20 LPA

Want me to help tailor your resume for any of these roles?"""

    elif any(w in message for w in ["project", "portfolio", "github", "idea"]):
        response = """**Portfolio Projects That Get You Hired (2025):**

**🏆 Top 5 AI-Era Projects:**

1. **RAG-based Chatbot** — LangChain + ChromaDB + Streamlit
   Impact: Shows you can work with LLMs — hiring boom right now

2. **End-to-End ML Pipeline** — Data → Train → Deploy on AWS
   Impact: Shows production ML knowledge, not just notebooks

3. **Real-time Dashboard** — WebSockets + React + FastAPI + PostgreSQL
   Impact: Shows full-stack ability, interviewers love live demos

4. **Resume Analyzer (like CVMatch!)** — NLP + spaCy + Python
   Impact: Meta-cool, directly relevant to the job you're applying for

5. **Micro-SaaS** — Any tool that solves a real problem
   Impact: Shows entrepreneurial thinking + product sense

**For each project:**
- Write a clear README with screenshots
- Host live on Hugging Face Spaces, Vercel, or Railway
- Add to GitHub + LinkedIn featured section
- Mention in resume with METRICS

Which one should I help you plan first?"""

    elif any(w in message for w in ["cover letter", "write", "letter"]):
        response = """**Cover Letter — AI-Optimized Template:**

---
**[Your Name]**
[Date]

Dear Hiring Manager,

I am writing to express my strong interest in the **[Role Name]** position at **[Company]**. As a B.Tech IT student with hands-on experience in **[Your Top 2-3 Skills]**, I am excited about the opportunity to contribute to **[Company's specific product/mission]**.

During my internship at **[Company]**, I **[specific achievement with metric]**, demonstrating my ability to deliver results in fast-paced environments. My project **[Project Name]** — which achieved **[metric]** — directly aligns with the technical requirements outlined in your job posting.

I am particularly drawn to **[Company]** because of **[specific reason: product, culture, growth stage]**. I am confident that my skills in **[2 key skills from JD]** would allow me to make an immediate impact.

Thank you for considering my application. I look forward to discussing how I can contribute to your team.

Warm regards,
**[Your Name]**

---

**Key Tips:**
- Keep it under 250 words — recruiters skim
- Mention the company name 2-3x to show genuine interest
- Mirror exact language from the job description
- End with a clear call to action

Want me to write a customized version for a specific job you're targeting?"""

    else:
        response = """I'm your AI career assistant — here to help with every step of your job search!

**What I can help you with:**

📊 **Resume & ATS** — Score analysis, rewriting, optimization
🎯 **Job Matching** — Find the best roles for your skills
💡 **Skill Roadmap** — What to learn next for your target role
🎙️ **Interview Prep** — Mock questions, company-specific tips
✍️ **Cover Letters** — Customized, ATS-optimized templates
🚀 **Career Strategy** — Salary negotiation, job search tactics

**Your Profile Snapshot:**
- ATS Score: **82/100** (↑ +12 from last scan)
- Job Matches: **247** (23 new today)
- Top Skills: Python, ML, React, SQL

What would you like to work on? You can ask me anything!"""

    return {
        "success": True,
        "response": response,
        "suggestions": [
            "Help me write a cover letter",
            "What skills should I add to my resume?",
            "Prepare me for a Google interview",
            "Find internships for a Python developer",
        ]
    }


# ── SKILLS EXTRACTION ─────────────────────────

@app.post("/api/skills/extract")
def extract_skills(request: ATSRequest):
    """Extract skills from any text."""
    skills = extract_skills_from_text(request.resume_text)
    return {
        "success": True,
        "skills": skills,
        "count": len(skills),
        "categories": {
            "languages": [s for s in skills if s in ["Python", "Java", "JavaScript", "TypeScript", "C++", "C", "Go", "Rust", "Kotlin", "Swift"]],
            "frameworks": [s for s in skills if s in ["React", "React.js", "Angular", "Vue.js", "Next.js", "Node.js", "Django", "FastAPI", "Flask"]],
            "ml_ai": [s for s in skills if s in ["Machine Learning", "Deep Learning", "TensorFlow", "PyTorch", "Scikit-learn", "NLP"]],
            "databases": [s for s in skills if s in ["SQL", "PostgreSQL", "MySQL", "MongoDB", "Redis"]],
            "cloud": [s for s in skills if s in ["AWS", "GCP", "Azure", "Docker", "Kubernetes"]],
        }
    }


# ── DASHBOARD STATS ───────────────────────────

@app.get("/api/dashboard/stats")
def get_dashboard_stats(user_id: str = "demo"):
    """Get dashboard statistics for the user."""
    return {
        "success": True,
        "stats": {
            "ats_score": 82,
            "ats_change": +12,
            "job_matches": 247,
            "new_matches_today": 23,
            "applications_sent": 8,
            "interview_calls": 3,
        },
        "recent_activity": [
            {"type": "scan", "message": "Resume re-scanned — ATS improved to 82", "time": "2h ago"},
            {"type": "apply", "message": "Applied to Software Engineer at Google", "time": "5h ago"},
            {"type": "match", "message": "247 new job matches found", "time": "1d ago"},
        ],
        "top_matches": [
            {"title": "Software Engineer", "company": "Google", "match": 94, "salary": "₹18-25 LPA"},
            {"title": "Data Analyst Intern", "company": "Razorpay", "match": 91, "salary": "₹25K/month"},
            {"title": "ML Engineer", "company": "Flipkart", "match": 88, "salary": "₹15-20 LPA"},
        ]
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
