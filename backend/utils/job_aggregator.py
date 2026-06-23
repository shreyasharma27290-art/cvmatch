"""
CVMatch Job Aggregator
Collects and normalises job listings from multiple platforms.

Supported sources (production):
  - LinkedIn Jobs  → Official Jobs API / job-feed RSS
  - Internshala    → Public listing pages (BeautifulSoup)
  - Naukri         → Partner API / RSS
  - Indeed         → Publisher API
  - Wellfound      → Public GraphQL API

This file ships with a full demo dataset so the frontend works
without any live API calls. Swap the demo helpers for the real
scrapers when you add API keys.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import random

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Normalised job schema
# ---------------------------------------------------------------------------

def make_job(
    title: str,
    company: str,
    location: str,
    job_type: str,
    source: str,
    source_url: str,
    salary_display: str,
    skills: List[str],
    description: str,
    requirements: List[str],
    exp_required: int = 0,
    tags: Optional[List[str]] = None,
    posted_days_ago: int = 0,
) -> Dict:
    return {
        "title": title,
        "company": company,
        "location": location,
        "job_type": job_type,          # full-time | internship | contract
        "source": source,              # linkedin | internshala | naukri | indeed | wellfound
        "source_url": source_url,
        "salary_display": salary_display,
        "skills": skills,
        "description": description,
        "requirements": requirements,
        "exp_required": exp_required,
        "tags": tags or [],
        "posted_at": (datetime.utcnow() - timedelta(days=posted_days_ago)).isoformat(),
        "is_active": True,
    }


# ---------------------------------------------------------------------------
# Demo dataset  (replace each section with a real scraper/API call)
# ---------------------------------------------------------------------------

DEMO_JOBS: List[Dict] = [

    # ── LinkedIn ─────────────────────────────────────────────────────────
    make_job(
        title="Software Engineer", company="Google", location="Bangalore / Remote",
        job_type="full-time", source="linkedin",
        source_url="https://www.linkedin.com/jobs/",
        salary_display="₹18–25 LPA",
        skills=["Python", "Java", "Algorithms", "System Design", "SQL", "Distributed Systems"],
        description="Join Google's core infrastructure team. Design, build and scale systems that serve billions of queries daily.",
        requirements=["B.Tech/M.Tech CS or related", "Strong DSA", "Experience with distributed systems"],
        exp_required=0, tags=["Top Company", "ESOP"], posted_days_ago=0,
    ),
    make_job(
        title="Data Science Engineer", company="Swiggy", location="Bangalore",
        job_type="full-time", source="linkedin",
        source_url="https://www.linkedin.com/jobs/",
        salary_display="₹12–18 LPA",
        skills=["Python", "Machine Learning", "SQL", "Data Analysis", "REST API", "Spark"],
        description="Work on demand forecasting, route optimisation and ETA prediction at massive scale.",
        requirements=["Strong Python & ML", "Large dataset experience", "Statistics knowledge"],
        exp_required=1, tags=["Growth Stage"], posted_days_ago=2,
    ),
    make_job(
        title="DevOps Engineer", company="PhonePe", location="Bangalore",
        job_type="full-time", source="linkedin",
        source_url="https://www.linkedin.com/jobs/",
        salary_display="₹12–18 LPA",
        skills=["Docker", "Kubernetes", "AWS", "CI/CD", "Python", "Linux", "Terraform"],
        description="Build and maintain the infrastructure powering India's largest UPI payment app.",
        requirements=["2+ yrs DevOps/SRE", "Docker & K8s proficiency", "Scripting skills"],
        exp_required=1, tags=["Fintech", "Scale"], posted_days_ago=1,
    ),
    make_job(
        title="AI Research Intern", company="Microsoft India", location="Hyderabad (Hybrid)",
        job_type="internship", source="linkedin",
        source_url="https://www.linkedin.com/jobs/",
        salary_display="₹60,000/month",
        skills=["Python", "Machine Learning", "Deep Learning", "PyTorch", "Research"],
        description="Work alongside world-class researchers on cutting-edge AI projects at Microsoft Research India.",
        requirements=["Final year B.Tech or pursuing Masters/PhD", "Strong ML & maths background"],
        exp_required=0, tags=["High Stipend", "PPO Opportunity", "Research"], posted_days_ago=1,
    ),

    # ── Internshala ──────────────────────────────────────────────────────
    make_job(
        title="Data Analyst Intern", company="Razorpay", location="Bangalore (Hybrid)",
        job_type="internship", source="internshala",
        source_url="https://internshala.com/",
        salary_display="₹25,000/month",
        skills=["Python", "SQL", "Excel", "Data Analysis", "Statistics", "Tableau"],
        description="Analyse payment trends, build dashboards and generate insights for product decisions. Ideal for final-year students.",
        requirements=["3rd/4th year B.Tech", "Strong SQL & Python", "Available 3–6 months"],
        exp_required=0, tags=["Stipend", "Certificate", "Flexible"], posted_days_ago=0,
    ),
    make_job(
        title="Python Developer Intern", company="Internshala", location="Remote",
        job_type="internship", source="internshala",
        source_url="https://internshala.com/",
        salary_display="₹10,000/month",
        skills=["Python", "Django", "REST API", "PostgreSQL", "Git"],
        description="Build internal tooling and automation scripts for Internshala's platform team.",
        requirements=["Basic Python knowledge", "Familiarity with web frameworks", "Git basics"],
        exp_required=0, tags=["Remote", "Beginner-friendly"], posted_days_ago=3,
    ),
    make_job(
        title="Data Analytics Intern", company="Deloitte India", location="Mumbai / Remote",
        job_type="internship", source="internshala",
        source_url="https://internshala.com/",
        salary_display="₹15,000/month",
        skills=["Excel", "SQL", "Power BI", "Data Analysis", "Python"],
        description="Support client analytics engagements across FMCG, banking and healthcare verticals.",
        requirements=["2nd year B.Tech or above", "Excel + SQL proficiency", "Attention to detail"],
        exp_required=0, tags=["MNC", "Stipend", "Certificate"], posted_days_ago=5,
    ),
    make_job(
        title="Web Development Intern", company="Zomato", location="Gurgaon (Hybrid)",
        job_type="internship", source="internshala",
        source_url="https://internshala.com/",
        salary_display="₹20,000/month",
        skills=["React.js", "JavaScript", "HTML", "CSS", "Node.js"],
        description="Build and improve features on Zomato's consumer-facing web app. Ship code that millions use.",
        requirements=["Strong React skills", "Portfolio of web projects", "3rd/4th year student"],
        exp_required=0, tags=["Stipend", "PPO Opportunity", "Hybrid"], posted_days_ago=2,
    ),

    # ── Naukri ───────────────────────────────────────────────────────────
    make_job(
        title="ML Engineer", company="Flipkart", location="Bangalore",
        job_type="full-time", source="naukri",
        source_url="https://www.naukri.com/",
        salary_display="₹15–20 LPA",
        skills=["Python", "TensorFlow", "Machine Learning", "Pandas", "AWS", "Spark"],
        description="Build recommendation, search ranking and fraud detection ML models at Flipkart scale.",
        requirements=["Strong ML fundamentals", "TensorFlow/PyTorch experience", "Cloud experience"],
        exp_required=0, tags=["Immediate Joining"], posted_days_ago=1,
    ),
    make_job(
        title="Python Backend Developer", company="Zerodha", location="Bangalore",
        job_type="full-time", source="naukri",
        source_url="https://www.naukri.com/",
        salary_display="₹10–15 LPA",
        skills=["Python", "FastAPI", "PostgreSQL", "REST API", "Git", "Redis"],
        description="Build high-performance trading APIs at India's largest stockbroker. Focus on low latency and reliability.",
        requirements=["Strong Python", "FastAPI or Flask experience", "Financial systems knowledge a plus"],
        exp_required=0, tags=["ESOP", "Stable", "No Layoffs"], posted_days_ago=3,
    ),
    make_job(
        title="Java Backend Engineer", company="Infosys Digital", location="Pune / Bangalore",
        job_type="full-time", source="naukri",
        source_url="https://www.naukri.com/",
        salary_display="₹6–10 LPA",
        skills=["Java", "Spring Boot", "Microservices", "SQL", "REST API", "Docker"],
        description="Develop enterprise-grade microservices for Infosys Digital clients across banking and insurance.",
        requirements=["Java 11+ proficiency", "Spring Boot experience", "Good DSA fundamentals"],
        exp_required=0, tags=["Mass Hiring", "Bond: 1 year"], posted_days_ago=0,
    ),

    # ── Indeed ───────────────────────────────────────────────────────────
    make_job(
        title="Full Stack Developer", company="Josh Technology Group", location="Gurgaon / Remote",
        job_type="full-time", source="indeed",
        source_url="https://www.indeed.com/",
        salary_display="₹8–12 LPA",
        skills=["React.js", "Node.js", "MongoDB", "REST API", "JavaScript", "TypeScript"],
        description="Build end-to-end web applications for enterprise clients. Own features from design to deployment.",
        requirements=["React & Node.js proficiency", "Database experience", "REST API expertise"],
        exp_required=0, tags=["Work from Home"], posted_days_ago=5,
    ),
    make_job(
        title="Data Engineer", company="Publicis Sapient", location="Bangalore / Remote",
        job_type="full-time", source="indeed",
        source_url="https://www.indeed.com/",
        salary_display="₹10–16 LPA",
        skills=["Python", "SQL", "Apache Spark", "AWS", "Airflow", "dbt", "Kafka"],
        description="Design and build scalable data pipelines for Fortune 500 clients in retail and banking.",
        requirements=["Python & SQL expertise", "ETL pipeline experience", "Cloud platform knowledge"],
        exp_required=1, tags=["Hybrid", "Global Exposure"], posted_days_ago=4,
    ),

    # ── Wellfound / AngelList ─────────────────────────────────────────────
    make_job(
        title="Frontend Developer Intern", company="CRED", location="Remote",
        job_type="internship", source="wellfound",
        source_url="https://wellfound.com/",
        salary_display="₹20,000/month",
        skills=["React.js", "TypeScript", "JavaScript", "CSS", "Next.js", "Git"],
        description="Build premium web experiences for CRED's members. Work directly with senior engineers and designers.",
        requirements=["Strong React experience", "Eye for design", "TypeScript familiarity"],
        exp_required=0, tags=["PPO Opportunity", "Startup Culture", "Design-focused"], posted_days_ago=0,
    ),
    make_job(
        title="AI/ML Engineer", company="Sarvam AI", location="Bangalore",
        job_type="full-time", source="wellfound",
        source_url="https://wellfound.com/",
        salary_display="₹15–30 LPA",
        skills=["Python", "PyTorch", "NLP", "LangChain", "Machine Learning", "Deep Learning"],
        description="Work on India's first large language model. Help build AI that truly understands Indian languages.",
        requirements=["Strong ML/DL background", "NLP experience preferred", "Research publications a plus"],
        exp_required=0, tags=["High Growth", "ESOP", "Cutting-edge AI"], posted_days_ago=1,
    ),
    make_job(
        title="Backend Engineer (Go/Python)", company="Groww", location="Bangalore",
        job_type="full-time", source="wellfound",
        source_url="https://wellfound.com/",
        salary_display="₹12–20 LPA",
        skills=["Go", "Python", "Microservices", "PostgreSQL", "Kafka", "Docker", "Kubernetes"],
        description="Build the backend powering India's largest investment platform serving 10M+ users.",
        requirements=["Go or Python proficiency", "Distributed systems knowledge", "Fintech interest"],
        exp_required=0, tags=["High Growth", "ESOP", "Fintech"], posted_days_ago=2,
    ),
]


# ---------------------------------------------------------------------------
# Aggregator Class
# ---------------------------------------------------------------------------

class JobAggregator:
    """
    Collects jobs from multiple sources, normalises them, and returns
    a unified list ready to be stored in PostgreSQL.

    In production replace each `_fetch_*` method with a real
    API call or scraper. The interface stays the same.
    """

    def __init__(self, use_demo: bool = True):
        self.use_demo = use_demo

    # ── Public API ──────────────────────────────────────────────────────

    async def fetch_all(
        self,
        keywords: Optional[List[str]] = None,
        location: str = "India",
        job_type: str = "all",
    ) -> List[Dict]:
        """Fetch from all sources concurrently and merge results."""
        tasks = [
            self._fetch_linkedin(keywords, location),
            self._fetch_internshala(keywords),
            self._fetch_naukri(keywords, location),
            self._fetch_indeed(keywords, location),
            self._fetch_wellfound(keywords),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        merged: List[Dict] = []
        for r in results:
            if isinstance(r, Exception):
                logger.warning(f"Source fetch failed: {r}")
            else:
                merged.extend(r)

        # Filter by job type
        if job_type == "internship":
            merged = [j for j in merged if j["job_type"] == "internship"]
        elif job_type == "full-time":
            merged = [j for j in merged if j["job_type"] == "full-time"]

        # Filter by keyword
        if keywords:
            kw_lower = [k.lower() for k in keywords]
            merged = [
                j for j in merged
                if any(k in j["title"].lower() or k in " ".join(j["skills"]).lower() for k in kw_lower)
            ]

        # Deduplicate by (title + company)
        seen = set()
        unique: List[Dict] = []
        for j in merged:
            key = (j["title"].lower(), j["company"].lower())
            if key not in seen:
                seen.add(key)
                unique.append(j)

        logger.info(f"Aggregated {len(unique)} unique jobs from {len(tasks)} sources")
        return unique

    def compute_match_scores(self, jobs: List[Dict], user_skills: List[str]) -> List[Dict]:
        """Add match_score and matched/missing skills to each job."""
        user_lower = {s.lower() for s in user_skills}
        scored: List[Dict] = []

        for job in jobs:
            job_skills = job.get("skills", [])
            matched = [s for s in job_skills if s.lower() in user_lower]
            missing = [s for s in job_skills if s.lower() not in user_lower]

            if job_skills:
                raw_pct = round(len(matched) / len(job_skills) * 100)
            else:
                raw_pct = 50

            # Add small variance for realism
            match_pct = min(97, max(20, raw_pct + random.randint(-3, 6)))

            scored.append({
                **job,
                "match_score": match_pct,
                "matched_skills": matched,
                "missing_skills": missing,
                "selection_probability": f"{match_pct}%",
            })

        # Sort by match descending
        scored.sort(key=lambda x: x["match_score"], reverse=True)
        return scored

    # ── Source Fetchers (stub → replace with real logic) ────────────────

    async def _fetch_linkedin(self, keywords, location) -> List[Dict]:
        """
        Production: call LinkedIn Jobs API with OAuth token.
        https://developer.linkedin.com/docs/guide/v2/jobs
        """
        await asyncio.sleep(0.1)  # simulate network latency
        if self.use_demo:
            return [j for j in DEMO_JOBS if j["source"] == "linkedin"]
        # --- PRODUCTION CODE (uncomment & fill in credentials) ---
        # async with aiohttp.ClientSession() as session:
        #     headers = {"Authorization": f"Bearer {LINKEDIN_TOKEN}"}
        #     params = {"keywords": " ".join(keywords or []), "location": location, "count": 25}
        #     async with session.get("https://api.linkedin.com/v2/jobSearch", headers=headers, params=params) as r:
        #         data = await r.json()
        #         return [self._normalise_linkedin(j) for j in data.get("elements", [])]
        return []

    async def _fetch_internshala(self, keywords) -> List[Dict]:
        """
        Production: scrape Internshala listing pages with BeautifulSoup.
        Rate-limit to 1 request / 3 seconds to be polite.
        """
        await asyncio.sleep(0.1)
        if self.use_demo:
            return [j for j in DEMO_JOBS if j["source"] == "internshala"]
        # --- PRODUCTION CODE ---
        # Base URL: https://internshala.com/internships/keywords-{keyword}/
        # Parse .individual_internship cards with bs4
        return []

    async def _fetch_naukri(self, keywords, location) -> List[Dict]:
        """
        Production: use Naukri's partner API or their XML job feed.
        """
        await asyncio.sleep(0.1)
        if self.use_demo:
            return [j for j in DEMO_JOBS if j["source"] == "naukri"]
        return []

    async def _fetch_indeed(self, keywords, location) -> List[Dict]:
        """
        Production: use Indeed Publisher API.
        https://developer.indeed.com/docs
        """
        await asyncio.sleep(0.1)
        if self.use_demo:
            return [j for j in DEMO_JOBS if j["source"] == "indeed"]
        return []

    async def _fetch_wellfound(self, keywords) -> List[Dict]:
        """
        Production: call Wellfound's public GraphQL API.
        """
        await asyncio.sleep(0.1)
        if self.use_demo:
            return [j for j in DEMO_JOBS if j["source"] == "wellfound"]
        return []

    # ── Normalisers (production) ─────────────────────────────────────────

    @staticmethod
    def _normalise_linkedin(raw: dict) -> Dict:
        return make_job(
            title=raw.get("title", ""),
            company=raw.get("companyName", ""),
            location=raw.get("formattedLocation", ""),
            job_type="full-time" if "full" in raw.get("employmentType", "").lower() else "internship",
            source="linkedin",
            source_url=raw.get("applyUrl", "https://linkedin.com/jobs"),
            salary_display=raw.get("salaryInsights", {}).get("compensationRange", "Not disclosed"),
            skills=raw.get("skills", []),
            description=raw.get("description", "")[:500],
            requirements=[],
        )

    @staticmethod
    def _normalise_internshala(raw: dict) -> Dict:
        return make_job(
            title=raw.get("profile_name", ""),
            company=raw.get("company_name", ""),
            location=raw.get("location_names", ["Remote"])[0],
            job_type="internship",
            source="internshala",
            source_url=f"https://internshala.com/internship/detail/{raw.get('id', '')}",
            salary_display=f"₹{raw.get('stipend', {}).get('salary', 'Unpaid')}/month",
            skills=raw.get("skills", []),
            description=raw.get("other_detail", "")[:500],
            requirements=[],
        )


# ---------------------------------------------------------------------------
# Quick CLI test
# ---------------------------------------------------------------------------

async def _demo():
    agg = JobAggregator(use_demo=True)
    jobs = await agg.fetch_all(keywords=["Python", "ML"], job_type="all")
    scored = agg.compute_match_scores(jobs, user_skills=["Python", "Machine Learning", "SQL", "React.js"])
    print(f"\nFetched {len(scored)} jobs:\n")
    for j in scored[:5]:
        print(f"  [{j['match_score']:3d}%] {j['title']:40s} @ {j['company']:20s}  ({j['source']})")


if __name__ == "__main__":
    asyncio.run(_demo())
