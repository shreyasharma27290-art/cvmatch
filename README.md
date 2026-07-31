# 🎯 CVMatch — AI Resume Analysis & Job Matching Platform

> **"Match Your Resume With The Right Opportunity."**

CVMatch is a full-stack, AI-powered career platform that helps students and professionals optimize their resumes, get instant ATS scores, discover matched jobs from 50+ platforms, and chat with an AI career assistant — all in one place.

---

## ✨ Features

| Feature | Description |
|---|---|
| 📊 **ATS Score Analysis** | 5-dimension scoring: Keywords, Skills, Formatting, Experience, Readability |
| 🎯 **Job Matching** | Cosine-similarity matching against LinkedIn, Internshala, Naukri, Indeed, Wellfound |
| 🤖 **AI Career Assistant** | Claude-powered chatbot for resume advice, interview prep, skill roadmaps |
| ✍️ **AI Resume Rewriter** | Paste a JD → get optimized bullet points with measurable impact |
| 📝 **Cover Letter Generator** | AI-written, role-specific cover letters in seconds |
| 🎓 **Internship Engine** | Personalized internship recommendations for students |
| 📈 **Skill Gap Analysis** | See exactly what skills to add for your target role |
| 💳 **Free + Premium Plans** | ₹0 free tier / ₹299/month for unlimited access |

---

## 🗂 Project Structure

```
cvmatch/
├── frontend/
│   ├── index.html              ← Landing page
│   ├── css/
│   │   └── styles.css          ← Global CSS (dark-tech theme)
│   └── pages/
│       ├── login.html          ← Auth page (Sign In / Sign Up)
│       ├── dashboard.html      ← Main user dashboard
│       ├── analyzer.html       ← Resume upload & ATS analysis
│       ├── jobs.html           ← Job & internship listings
│       ├── chatbot.html        ← AI career assistant chat
│       └── profile.html        ← Profile & settings
│
├── backend/
│   ├── main.py                 ← FastAPI app (all routes)
│   ├── models.py               ← SQLAlchemy database models
│   ├── requirements.txt        ← Python dependencies
│   └── utils/
│       ├── resume_parser.py    ← PDF/DOCX text extraction
│       ├── ats_engine.py       ← ATS scoring algorithm
│       └── job_aggregator.py   ← Multi-source job fetcher
│
├── .env.example                ← Environment variable template
└── README.md
```

---

## 🚀 Quick Start

### 1. Clone & setup

```bash
git clone https://github.com/your-username/cvmatch.git
cd cvmatch
```

### 2. Frontend (open directly in browser)

```bash
# No build step needed — pure HTML/CSS/JS
open frontend/index.html
# Or serve with a simple server:
npx serve frontend -p 3000
```

### 3. Backend (Python FastAPI)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install spaCy language model
python -m spacy download en_core_web_sm

# Copy and fill in environment variables
cp ../.env.example .env
# → Edit .env with your API keys

# Start the server
uvicorn main:app --reload --port 8000
```

API docs available at: **http://localhost:8000/api/docs**

---

## 🛠 Tech Stack

### Frontend
- **HTML5 + CSS3 + Vanilla JavaScript** — zero framework dependencies
- **Space Grotesk + Inter** fonts via Google Fonts
- **CSS Custom Properties** for the dark-tech theme
- **SVG animations** for score rings and loading states

### Backend
- **FastAPI** — async Python web framework
- **SQLAlchemy** — ORM with PostgreSQL support
- **pdfplumber / python-docx** — resume text extraction
- **spaCy** — NLP for skill detection
- **Anthropic Claude API** — AI career assistant & resume rewriting
- **Pinecone** — vector database for semantic job matching

### Infrastructure (Production)
- **Frontend** → Vercel (auto-deploy from GitHub)
- **Backend** → Render or Railway
- **Database** → Neon PostgreSQL (serverless)
- **Storage** → AWS S3 (resume files)
- **Vector DB** → Pinecone

---

## 🔌 API Reference

### Resume Analysis
```
POST /api/resume/analyze        Upload PDF/DOCX → full ATS report
POST /api/resume/ats-score      Raw text → ATS score
POST /api/resume/match-job      Resume + JD → match percentage
POST /api/resume/improve        Get AI rewrite suggestions
```

### Jobs
```
POST /api/jobs/recommend        Skills list → ranked job matches
GET  /api/jobs/search           Search with filters
GET  /api/jobs/{id}             Job detail
```

### AI Chat
```
POST /api/chat                  Career assistant conversation
```

### Auth
```
POST /api/auth/register         Create account
POST /api/auth/login            Sign in
```

### Skills & Dashboard
```
POST /api/skills/extract        Extract skills from text
GET  /api/dashboard/stats       User dashboard data
```

---

## 📊 ATS Scoring Algorithm

```
Total Score = Keywords (35) + Skills (25) + Formatting (20) + Experience (12) + Readability (8)
                                                                                              ───
                                                                                              100
```

**Keywords (35 pts):** High-value action verbs, JD keyword overlap, terminology density

**Skills (25 pts):** Number of detected tech skills × variety across categories

**Formatting (20 pts):** Bullet points, quantified achievements, action verbs, ATS-safe layout

**Experience (12 pts):** Work/internship presence, date ranges, project section

**Readability (8 pts):** Sentence length, complexity, structure clarity

---

## 🌐 Job Sources

| Platform | Type | Method |
|---|---|---|
| LinkedIn | Jobs + Internships | Official Jobs API |
| Internshala | Internships | BeautifulSoup scraper |
| Naukri | Jobs | Partner XML feed |
| Indeed | Jobs | Publisher API |
| Wellfound | Startup jobs | Public GraphQL |
| Glassdoor | Jobs | RSS / API |

> ⚠️ Always check each platform's Terms of Service before enabling live scraping.
> The project ships with a full demo dataset so you can develop without API keys.

---

## 💰 Pricing

| | Free | Premium |
|---|---|---|
| Resume Scans | 3 / month | Unlimited |
| ATS Reports | ✓ | ✓ |
| Job Matches | 10 | Unlimited |
| AI Chat | 10 messages | Unlimited |
| Resume Rewriter | ✗ | ✓ |
| Cover Letter AI | ✗ | ✓ |
| Interview Coach | ✗ | ✓ (Soon) |
| **Price** | **₹0** | **₹299 / month** |

---

## 🗺 Roadmap

### v1.0 — MVP (Current)
- [x] Resume upload & ATS scoring
- [x] Job matching with multi-source aggregation
- [x] AI career assistant chatbot
- [x] Dashboard with analytics
- [x] Job/internship recommendations
- [x] Profile & settings

### v2.0 — Coming Soon
- [ ] AI Mock Interview (voice + scoring)
- [ ] Auto-Apply Assistant
- [ ] AI Cover Letter Generator (one-click)
- [ ] Full AI Resume Builder
- [ ] Real-time job scraping pipeline
- [ ] Recruiter portal
- [ ] Mobile app (React Native)

---

## 👨‍💻 For B.Tech Students

This project is designed to be built incrementally. If you're a B.Tech IT student:

1. **Week 1-2:** Get the frontend running. Understand the HTML/CSS structure.
2. **Week 3-4:** Set up FastAPI backend. Test `/api/resume/ats-score`.
3. **Week 5-6:** Integrate Claude API for the chatbot.
4. **Week 7-8:** Add Pinecone for semantic job matching.
5. **Week 9-10:** Deploy frontend to Vercel, backend to Render.
6. **Week 11-12:** Add payments (Razorpay) and launch!

---
## Current Status

CVMatch is currently an MVP/full-stack prototype.

### Working
- Responsive frontend pages
- FastAPI backend structure
- Resume parser utility
- ATS scoring logic
- Job matching API with demo dataset
- Dashboard and AI career assistant UI

### In Progress
- Connecting frontend analyzer with backend API
- Real PDF/DOCX parsing in live deployment
- Backend-based AI chatbot integration
- Database persistence
- Production deployment of FastAPI backend

  ---
### Demo Data Notice
Some job listings, pricing, user statistics, and AI responses are sample/demo data used for project demonstration.
## 📄 License

MIT License — free to use, modify, and build on.

---

Built with ❤️ for India's student developer community.
