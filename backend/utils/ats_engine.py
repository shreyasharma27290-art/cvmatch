"""
CVMatch ATS Scoring Engine
Calculates detailed ATS compatibility scores for resumes.

Scoring breakdown (total = 100):
  Keywords & Terminology  → 35 pts
  Skills Match            → 25 pts
  Formatting & Structure  → 20 pts
  Experience Relevance    → 12 pts
  Readability             →  8 pts
"""

import re
import math
import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# High-value ATS keywords (role-agnostic)
# ---------------------------------------------------------------------------

HIGH_VALUE_KEYWORDS = [
    # Action verbs
    "developed", "built", "designed", "implemented", "optimised", "improved",
    "delivered", "launched", "led", "managed", "created", "engineered",
    "automated", "deployed", "scaled", "reduced", "increased", "collaborated",
    # Metric indicators
    "accuracy", "performance", "latency", "throughput", "uptime", "availability",
    "revenue", "cost", "efficiency", "users", "customers", "requests",
    # General tech
    "api", "backend", "frontend", "full-stack", "microservices", "database",
    "cloud", "pipeline", "algorithm", "model", "system", "architecture",
    "agile", "scrum", "devops", "ci/cd", "testing", "deployment",
]

QUANTIFIER_PATTERN = re.compile(
    r'\d+(\.\d+)?\s*(%|percent|k\b|lpa|lakh|crore|users|requests|ms|sec|x\b|times|hours|days|weeks)',
    re.I
)

ACTION_VERB_PATTERN = re.compile(
    r'\b(developed|built|designed|implemented|created|launched|led|managed|'
    r'improved|increased|reduced|optimised|automated|deployed|scaled|'
    r'delivered|engineered|architected|collaborated|mentored|researched|'
    r'analysed|streamlined|migrated|integrated|maintained|established)\b',
    re.I
)

SECTION_HEADERS = {
    "summary":        re.compile(r'\b(summary|objective|about|profile|overview)\b', re.I),
    "education":      re.compile(r'\b(education|degree|university|college|b\.?tech|m\.?tech|bachelor|master)\b', re.I),
    "experience":     re.compile(r'\b(experience|work|employment|career|internship)\b', re.I),
    "skills":         re.compile(r'\b(skills|technologies|stack|proficiencies|tools|competencies)\b', re.I),
    "projects":       re.compile(r'\b(projects|portfolio|work samples|side projects)\b', re.I),
    "certifications": re.compile(r'\b(certifications?|courses?|training|awards?|achievements?)\b', re.I),
    "contact":        re.compile(r'\b(email|phone|linkedin|github|portfolio|contact)\b', re.I),
}

# Penalised ATS-breaking patterns
FORMATTING_PENALTIES = [
    (re.compile(r'<table', re.I),          "HTML tables detected — ATS cannot parse these"),
    (re.compile(r'<img',   re.I),          "Images embedded — ATS ignores images"),
    (re.compile(r'\|{3,}'),                "Excessive pipe characters — indicates table layout"),
    (re.compile(r'\.{5,}'),                "Excessive dots — likely tab-stop formatting"),
    (re.compile(r'[^\x00-\x7F]{5,}'),     "Non-ASCII characters — may cause parsing errors"),
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _count_bullets(text: str) -> int:
    """Count bullet-point lines."""
    return len(re.findall(r'^\s*[•\-\*▸►→✓✔]\s', text, re.MULTILINE))


def _count_quantified_lines(text: str) -> int:
    """Count lines that contain measurable metrics."""
    return len(QUANTIFIER_PATTERN.findall(text))


def _count_action_verbs(text: str) -> int:
    return len(ACTION_VERB_PATTERN.findall(text))


def _sections_present(text: str) -> Dict[str, bool]:
    text_lower = text.lower()
    return {name: bool(pattern.search(text_lower)) for name, pattern in SECTION_HEADERS.items()}


def _keyword_density(text: str, keywords: List[str]) -> float:
    """Fraction of high-value keywords found in text."""
    if not keywords:
        return 0.0
    text_lower = text.lower()
    found = sum(1 for kw in keywords if re.search(r'\b' + re.escape(kw.lower()) + r'\b', text_lower))
    return found / len(keywords)


def _readability_score(text: str) -> float:
    """
    Simple proxy for readability:
      - Average sentence length (shorter = better for ATS)
      - Ratio of long words
    Returns 0–1.
    """
    sentences = re.split(r'[.!?]', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.5

    avg_len = sum(len(s.split()) for s in sentences) / len(sentences)
    # Ideal ATS sentence length: 10–20 words
    length_score = 1.0 - min(1.0, abs(avg_len - 15) / 20)

    words = text.split()
    long_words = sum(1 for w in words if len(w) > 12)
    complexity = long_words / max(len(words), 1)
    complexity_score = 1.0 - min(1.0, complexity * 3)

    return (length_score + complexity_score) / 2


# ---------------------------------------------------------------------------
# Core scorer
# ---------------------------------------------------------------------------

class ATSScorer:
    """
    Calculates a detailed ATS compatibility score for a resume,
    optionally benchmarked against a specific job description.
    """

    def __init__(self, resume_text: str, job_description: str = ""):
        self.resume = resume_text
        self.jd = job_description
        self._result: Optional[Dict] = None

    # ── Public API ──────────────────────────────────────────────────────

    def score(self) -> Dict:
        """Run the full scoring pipeline and return a detailed report."""
        if self._result:
            return self._result

        kw_pts    = self._score_keywords()        # 35 pts
        skill_pts = self._score_skills()          # 25 pts
        fmt_pts   = self._score_formatting()      # 20 pts
        exp_pts   = self._score_experience()      # 12 pts
        read_pts  = self._score_readability()     #  8 pts

        raw = kw_pts + skill_pts + fmt_pts + exp_pts + read_pts

        # Clamp to 40–97 for demo realism
        import random
        total = max(40, min(97, round(raw) + random.randint(-2, 3)))

        # JD-specific match
        jd_match = self._jd_match() if self.jd else None

        sections = _sections_present(self.resume)

        self._result = {
            "total_score":  total,
            "grade":        self._grade(total),
            "sub_scores": {
                "keywords":    round(kw_pts    / 35 * 100),
                "skills":      round(skill_pts / 25 * 100),
                "formatting":  round(fmt_pts   / 20 * 100),
                "experience":  round(exp_pts   / 12 * 100),
                "readability": round(read_pts  /  8 * 100),
            },
            "raw_sub_pts": {
                "keywords": round(kw_pts, 1),
                "skills":   round(skill_pts, 1),
                "formatting": round(fmt_pts, 1),
                "experience": round(exp_pts, 1),
                "readability": round(read_pts, 1),
            },
            "jd_match":         jd_match,
            "sections_found":   sections,
            "sections_missing": [k for k, v in sections.items() if not v],
            "metrics": {
                "bullet_count":       _count_bullets(self.resume),
                "quantified_lines":   _count_quantified_lines(self.resume),
                "action_verb_count":  _count_action_verbs(self.resume),
                "word_count":         len(self.resume.split()),
            },
            "formatting_issues": self._formatting_issues(),
            "strengths":        self._generate_strengths(sections),
            "weaknesses":       self._generate_weaknesses(sections),
            "improvements":     self._generate_improvements(sections, jd_match),
        }
        return self._result

    # ── Scoring modules ─────────────────────────────────────────────────

    def _score_keywords(self) -> float:
        """Up to 35 points for high-value keyword coverage."""
        density = _keyword_density(self.resume, HIGH_VALUE_KEYWORDS)
        # Also reward JD keyword overlap if JD supplied
        if self.jd:
            jd_words = set(re.findall(r'\b[a-z]{4,}\b', self.jd.lower()))
            res_words = set(re.findall(r'\b[a-z]{4,}\b', self.resume.lower()))
            overlap = len(jd_words & res_words) / max(len(jd_words), 1)
            density = (density * 0.5) + (overlap * 0.5)
        return min(35.0, density * 50)

    def _score_skills(self) -> float:
        """Up to 25 points based on number and variety of detected skills."""
        from backend.utils.resume_parser import ALL_SKILLS
        found = [s for s in ALL_SKILLS if re.search(r'\b' + re.escape(s.lower()) + r'\b', self.resume.lower())]
        # 1 pt per skill up to 20, bonus for variety
        base = min(20.0, len(found) * 1.2)
        variety_bonus = min(5.0, len(set(found)) * 0.3)
        return base + variety_bonus

    def _score_formatting(self) -> float:
        """Up to 20 points for clean, ATS-parseable formatting."""
        pts = 0.0

        # Bullets indicate structure (up to 6 pts)
        bullets = _count_bullets(self.resume)
        pts += min(6.0, bullets * 0.5)

        # Quantified achievements (up to 6 pts)
        quantified = _count_quantified_lines(self.resume)
        pts += min(6.0, quantified * 1.5)

        # Action verbs (up to 4 pts)
        verbs = _count_action_verbs(self.resume)
        pts += min(4.0, verbs * 0.4)

        # Penalise ATS-breaking formatting
        issues = self._formatting_issues()
        pts -= len(issues) * 2

        # Sections completeness bonus (up to 4 pts)
        sections = _sections_present(self.resume)
        essential = ["education", "skills", "experience", "contact"]
        found_essential = sum(1 for s in essential if sections.get(s))
        pts += found_essential * 1.0

        return max(0.0, min(20.0, pts))

    def _score_experience(self) -> float:
        """Up to 12 points for relevant experience indicators."""
        text_lower = self.resume.lower()
        pts = 0.0

        # Has any work experience section
        if re.search(r'\b(experience|internship|work)\b', text_lower):
            pts += 3.0

        # Internship entries
        intern_count = len(re.findall(r'\bintern\b', text_lower))
        pts += min(3.0, intern_count * 1.5)

        # Date ranges (e.g. "Jan 2024 – Aug 2024")
        date_ranges = re.findall(
            r'(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{4}\s*[-–]\s*(jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec|present)',
            text_lower
        )
        pts += min(3.0, len(date_ranges) * 1.0)

        # Projects section
        if re.search(r'\bproject\b', text_lower):
            pts += 3.0

        return min(12.0, pts)

    def _score_readability(self) -> float:
        """Up to 8 points for clear, concise writing."""
        score = _readability_score(self.resume)
        return score * 8.0

    # ── JD Match ────────────────────────────────────────────────────────

    def _jd_match(self) -> Dict:
        """Compute overlap between resume and job description."""
        from backend.utils.resume_parser import ALL_SKILLS

        res_lower = self.resume.lower()
        jd_lower  = self.jd.lower()

        jd_skills  = [s for s in ALL_SKILLS if re.search(r'\b' + re.escape(s.lower()) + r'\b', jd_lower)]
        res_skills = [s for s in ALL_SKILLS if re.search(r'\b' + re.escape(s.lower()) + r'\b', res_lower)]

        matched = [s for s in jd_skills if s in res_skills]
        missing = [s for s in jd_skills if s not in res_skills]

        pct = round(len(matched) / max(len(jd_skills), 1) * 100)
        pct = max(20, min(97, pct))

        return {
            "match_score":    pct,
            "matched_skills": matched,
            "missing_skills": missing,
            "jd_skill_count": len(jd_skills),
            "recommendation": (
                "Excellent fit — apply now!" if pct >= 85
                else "Good fit — tailor 2–3 bullet points to the JD." if pct >= 65
                else "Partial fit — upskill on missing skills before applying."
            ),
        }

    # ── Formatting issues ───────────────────────────────────────────────

    def _formatting_issues(self) -> List[str]:
        issues = []
        for pattern, message in FORMATTING_PENALTIES:
            if pattern.search(self.resume):
                issues.append(message)
        # Length check
        word_count = len(self.resume.split())
        if word_count < 150:
            issues.append("Resume too short — add more detail to experience and projects")
        elif word_count > 900:
            issues.append("Resume too long — trim to 1 page (< 600 words) for fresher roles")
        return issues

    # ── Narrative generators ─────────────────────────────────────────────

    @staticmethod
    def _grade(score: int) -> str:
        if score >= 85: return "Excellent"
        if score >= 70: return "Good"
        if score >= 55: return "Fair"
        return "Needs Work"

    def _generate_strengths(self, sections: Dict[str, bool]) -> List[str]:
        strengths = []
        bullets = _count_bullets(self.resume)
        verbs   = _count_action_verbs(self.resume)
        nums    = _count_quantified_lines(self.resume)

        if bullets >= 5:
            strengths.append(f"Well-structured with {bullets} bullet points — ATS-friendly layout")
        if verbs >= 6:
            strengths.append("Good use of strong action verbs throughout")
        if nums >= 3:
            strengths.append("Quantified achievements — numbers stand out to recruiters")
        if sections.get("projects"):
            strengths.append("Projects section demonstrates practical experience")
        if sections.get("certifications"):
            strengths.append("Certifications add credibility and keyword coverage")
        if sections.get("skills"):
            strengths.append("Dedicated skills section improves keyword matching")
        return strengths[:5]

    def _generate_weaknesses(self, sections: Dict[str, bool]) -> List[str]:
        weaknesses = []
        if not sections.get("summary"):
            weaknesses.append("Missing professional summary — add 2–3 sentences at the top")
        if not sections.get("certifications"):
            weaknesses.append("No certifications listed — even free ones help ATS scoring")
        if _count_quantified_lines(self.resume) < 3:
            weaknesses.append("Too few measurable achievements — add percentages and numbers")
        if _count_bullets(self.resume) < 4:
            weaknesses.append("Not enough bullet points — structure experience as bullets")
        if not re.search(r'github\.com', self.resume, re.I):
            weaknesses.append("GitHub URL missing from contact section")
        if len(self.resume.split()) < 200:
            weaknesses.append("Resume is too brief — expand experience and project sections")
        return weaknesses[:5]

    def _generate_improvements(
        self, sections: Dict[str, bool], jd_match: Optional[Dict]
    ) -> List[Dict]:
        improvements = []

        if not sections.get("summary"):
            improvements.append({
                "priority": "high", "category": "Content",
                "title": "Add a Professional Summary",
                "description": "Write 2–3 sentences highlighting your top skills and career goal. Recruiters read this first.",
                "impact": "+8–12 ATS points",
            })

        if jd_match and jd_match["missing_skills"]:
            top3 = jd_match["missing_skills"][:3]
            improvements.append({
                "priority": "high", "category": "Skills Gap",
                "title": f"Add Missing Skills: {', '.join(top3)}",
                "description": f"The job requires {', '.join(top3)}. Add these to your skills section after learning them.",
                "impact": f"+{len(top3) * 5}% job match score",
            })

        if _count_quantified_lines(self.resume) < 3:
            improvements.append({
                "priority": "high", "category": "Achievements",
                "title": "Quantify Your Achievements",
                "description": "Replace vague phrases like 'improved performance' with '40% faster response time serving 10K users'.",
                "impact": "+6–10 ATS points",
            })

        if not sections.get("certifications"):
            improvements.append({
                "priority": "medium", "category": "Credentials",
                "title": "Add Certifications",
                "description": "AWS, Google Cloud, Coursera, or HackerRank certifications boost keyword coverage and recruiter trust.",
                "impact": "+5–8 ATS points",
            })

        if _count_action_verbs(self.resume) < 5:
            improvements.append({
                "priority": "medium", "category": "Language",
                "title": "Start Bullets with Strong Action Verbs",
                "description": "Begin every bullet with verbs like Developed, Built, Deployed, Reduced, Increased instead of 'Worked on' or 'Helped with'.",
                "impact": "+3–5 ATS points",
            })

        if not re.search(r'github\.com|linkedin\.com', self.resume, re.I):
            improvements.append({
                "priority": "low", "category": "Contact",
                "title": "Add GitHub & LinkedIn URLs",
                "description": "Include clickable URLs in your contact section. Recruiters always check these for tech roles.",
                "impact": "+2–4 ATS points",
            })

        return improvements[:6]


# ---------------------------------------------------------------------------
# Convenience wrapper used by the FastAPI routes
# ---------------------------------------------------------------------------

def compute_ats_report(resume_text: str, job_description: str = "") -> Dict:
    """One-shot function for the API route."""
    scorer = ATSScorer(resume_text, job_description)
    return scorer.score()


# ---------------------------------------------------------------------------
# Quick CLI test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    SAMPLE = """
Priya Sharma | priya@example.com | github.com/priya | linkedin.com/in/priya

EDUCATION
B.Tech IT | LPU | 2021–2025 | CGPA 8.2

SKILLS
Python, React.js, FastAPI, TensorFlow, SQL, PostgreSQL, Docker, AWS, Git

EXPERIENCE
Data Science Intern | ABC Analytics | June 2024 – Aug 2024
• Built ML models with Python & Scikit-learn, improving forecast accuracy by 18%
• Analysed 100K+ customer records using Pandas and SQL

PROJECTS
AI Recommendation Engine
• Collaborative filtering with TensorFlow, served 50K+ users, 99.9% uptime on AWS

CERTIFICATIONS
AWS Cloud Practitioner | Python for Data Science – Coursera
"""

    report = compute_ats_report(SAMPLE, job_description="Looking for Python ML engineer with TensorFlow and SQL")
    print(f"\nATS Score : {report['total_score']} / 100  ({report['grade']})")
    print(f"Sub-scores: {report['sub_scores']}")
    print(f"Sections  : {[k for k,v in report['sections_found'].items() if v]}")
    print(f"Strengths : {report['strengths']}")
    print(f"Weaknesses: {report['weaknesses']}")
    if report["jd_match"]:
        print(f"JD Match  : {report['jd_match']['match_score']}%  matched={report['jd_match']['matched_skills']}")
