"""
SkillLens RAG Knowledge Base
==============================
Lightweight Retrieval-Augmented Generation (RAG) module.
Stores rich career knowledge documents as chunked text records.
Uses TF-IDF-style keyword scoring for retrieval (no external vector DB needed).

Usage:
    from app.services.rag_knowledge import retrieve_context
    chunks = retrieve_context("machine learning career path", top_k=5)
    context_str = "\\n\\n".join(c["text"] for c in chunks)
"""

import re
import math
from typing import List, Dict, Any


# ─────────────────────────────────────────────────────────────────────────────
# Knowledge Documents
# Each document: { "id", "category", "tags": [...], "text": "..." }
# ─────────────────────────────────────────────────────────────────────────────

KNOWLEDGE_BASE: List[Dict[str, Any]] = [

    # ── AI / ML ──────────────────────────────────────────────────────────────
    {
        "id": "ai_eng_overview",
        "category": "career_path",
        "tags": ["AI engineer", "machine learning", "deep learning", "career"],
        "text": """
AI Engineer Career Overview
An AI Engineer designs, builds and deploys machine learning models and intelligent systems.
Core skills: Python, NumPy, Pandas, Scikit-learn, TensorFlow or PyTorch, MLOps, Vector Databases, LLMs (GPT/Llama), REST APIs.
Nice-to-have: Docker, Kubernetes, Cloud (AWS SageMaker / GCP Vertex AI / Azure ML), Statistics, SQL.
Recommended certifications: DeepLearning.AI specializations (Coursera), Google Professional ML Engineer, AWS ML Specialty.
Average time to job-ready from scratch: 8-12 months with 2-3 hrs/day study.
Fresher salary (India): ₹6-12 LPA. Mid-level: ₹15-35 LPA. Senior: ₹40-80+ LPA.
Top companies hiring: Google, Microsoft, Amazon, Flipkart, Juspay, Sarvam AI, CRED, Ola, startups in GenAI space.
Typical entry roles: ML Engineer, AI Research Engineer, NLP Engineer, Junior Data Scientist.
""",
    },
    {
        "id": "ai_learning_path",
        "category": "learning_path",
        "tags": ["AI engineer", "machine learning", "roadmap", "learning", "courses"],
        "text": """
AI/ML Learning Roadmap (Beginner → Job-Ready)
Phase 1 – Foundations (Month 1-2):
  - Python basics: OOP, file I/O, list comprehensions
  - Mathematics: Linear Algebra (3Blue1Brown YouTube), Calculus basics, Statistics
  - Resources: CS50P (Python), Khan Academy Math, fast.ai Practical Deep Learning (free)

Phase 2 – Core ML (Month 2-4):
  - Scikit-learn: regression, classification, clustering, pipelines
  - Data wrangling: Pandas, NumPy, Matplotlib, Seaborn
  - Projects: Titanic prediction (Kaggle), House price regression, Customer churn model
  - Resources: Coursera ML Specialization by Andrew Ng, Kaggle free courses

Phase 3 – Deep Learning (Month 4-6):
  - Neural networks, CNNs, RNNs, Transformers
  - PyTorch or TensorFlow
  - Projects: Image classifier, Sentiment analysis NLP model, Fine-tune small LLM
  - Resources: fast.ai, DeepLearning.AI Specializations, Hugging Face tutorials

Phase 4 – LLMs & Deployment (Month 6-8):
  - LangChain, LlamaIndex, RAG systems, prompt engineering
  - MLOps: MLflow, Docker, FastAPI model serving
  - Cloud: AWS SageMaker or GCP Vertex AI
  - Capstone: Build a RAG-powered chatbot with a vector database
""",
    },
    {
        "id": "data_scientist_overview",
        "category": "career_path",
        "tags": ["data scientist", "analytics", "statistics", "career"],
        "text": """
Data Scientist Career Overview
A Data Scientist extracts insights from data using statistical and ML techniques to drive business decisions.
Core skills: Python (Pandas, NumPy, Scikit-learn), SQL, Statistics, Data Visualization (Matplotlib, Seaborn, Tableau/Power BI), Machine Learning.
Nice-to-have: R, Apache Spark, A/B Testing, Experiment Design, Deep Learning, Cloud data warehouses (BigQuery, Snowflake).
Certifications: IBM Data Science Professional (Coursera), Google Data Analytics Certificate, DataCamp Career Tracks.
Time to ready: 6-10 months.
Salary (India fresher): ₹5-10 LPA. Mid: ₹12-30 LPA. Senior: ₹35-70+ LPA.
Companies: FAANG, fintech (Razorpay, PhonePe), e-commerce (Meesho, Myntra), consulting firms, analytics startups.
""",
    },

    # ── Full Stack ────────────────────────────────────────────────────────────
    {
        "id": "fullstack_overview",
        "category": "career_path",
        "tags": ["full stack developer", "web development", "react", "node.js", "career"],
        "text": """
Full Stack Developer Career Overview
A Full Stack Developer builds both frontend (UI) and backend (server, database) of web applications.
Core skills: HTML, CSS, JavaScript (ES6+), React or Vue or Angular, Node.js with Express, SQL (PostgreSQL/MySQL) and/or NoSQL (MongoDB), REST APIs, Git/GitHub.
Nice-to-have: TypeScript, Docker, CI/CD (GitHub Actions), GraphQL, AWS/GCP, Jest/Testing, Redis.
Certifications: Meta Frontend Developer Certificate (Coursera), AWS Developer Associate, MongoDB Developer Certification.
Time to ready: 4-8 months.
Salary (India fresher): ₹4-8 LPA. Mid: ₹10-22 LPA. Senior: ₹25-55+ LPA.
Companies: Product startups, SaaS companies, IT services (TCS, Infosys, Wipro), big tech (Google, Microsoft, Amazon).
""",
    },
    {
        "id": "fullstack_learning",
        "category": "learning_path",
        "tags": ["full stack", "web development", "react", "node", "learning"],
        "text": """
Full Stack Development Learning Path
Month 1: HTML/CSS/JavaScript fundamentals
  - Build a personal portfolio website, landing pages
  - Resources: The Odin Project (free, excellent), freeCodeCamp Responsive Web Design, MDN Web Docs
Month 2-3: React and REST APIs
  - React components, hooks, state, React Router
  - Connect to public APIs (OpenWeatherMap, etc.)
  - Projects: Todo app, weather app, Hacker News clone
  - Resources: React official docs, Scrimba React course, Full Stack Open (free, University of Helsinki)
Month 3-4: Node.js and Databases
  - Express.js server, REST API design, JWT auth
  - PostgreSQL with Prisma or Sequelize ORM
  - MongoDB with Mongoose
  - Projects: Blog API, authentication system
Month 4-6: Deployment and DevOps Basics
  - Docker basics, deploying to Render/Railway/Vercel/Netlify
  - CI/CD with GitHub Actions
  - Capstone: Full MERN/PERN stack SaaS app with auth, payments (Stripe), deployed to cloud
""",
    },

    # ── Cloud / DevOps ────────────────────────────────────────────────────────
    {
        "id": "cloud_engineer_overview",
        "category": "career_path",
        "tags": ["cloud engineer", "AWS", "Azure", "GCP", "DevOps", "career"],
        "text": """
Cloud Engineer / DevOps Engineer Career Overview
Cloud Engineers design and maintain cloud infrastructure. DevOps Engineers bridge development and operations with automation.
Core skills: Linux command line, Networking fundamentals (TCP/IP, DNS, HTTP), AWS/Azure/GCP, Terraform (Infrastructure as Code), Docker, Kubernetes, Python/Bash scripting.
Nice-to-have: Ansible, CI/CD (Jenkins, GitHub Actions, GitLab CI), Prometheus/Grafana monitoring, Service Meshes (Istio), Serverless (Lambda/Cloud Functions).
Certifications: AWS Solutions Architect Associate (most valued), Azure Administrator AZ-104, GCP Associate Cloud Engineer, CKA (Kubernetes Administrator).
Time to ready: 6-10 months.
Salary (India fresher): ₹5-10 LPA. Mid: ₹14-28 LPA. Senior: ₹30-65+ LPA.
Companies: All large tech companies, consulting (Accenture, Deloitte), cloud-native startups, IT services.
""",
    },

    # ── Cybersecurity ─────────────────────────────────────────────────────────
    {
        "id": "cybersecurity_overview",
        "category": "career_path",
        "tags": ["cybersecurity", "security analyst", "ethical hacking", "penetration testing", "career"],
        "text": """
Cybersecurity Analyst Career Overview
Cybersecurity Analysts protect organizations from digital threats.
Core skills: Networking (OSI model, TCP/IP, firewalls), Linux, Python for scripting, SIEM tools (Splunk, IBM QRadar), Penetration Testing basics, Risk Assessment, Vulnerability Management.
Nice-to-have: Ethical Hacking (Metasploit, Burp Suite), Digital Forensics, Cloud Security, Compliance frameworks (ISO 27001, SOC 2, GDPR).
Certifications: CompTIA Security+ (entry, most recommended first), CEH (Certified Ethical Hacker), OSCP (advanced, highly valued), CISSP (senior).
Time to ready: 6-12 months.
Salary (India fresher): ₹4-9 LPA. Mid: ₹12-25 LPA. Senior: ₹28-60+ LPA.
Companies: Banks/fintech (security critical), IT services, government PSUs, security firms (Quick Heal, Kaspersky, Palo Alto), large enterprises.
Learning platforms: TryHackMe (free/paid, gamified, excellent for beginners), HackTheBox, PortSwigger Web Security Academy.
""",
    },

    # ── Product Management ────────────────────────────────────────────────────
    {
        "id": "product_manager_overview",
        "category": "career_path",
        "tags": ["product manager", "PM", "product strategy", "career"],
        "text": """
Product Manager Career Overview
A Product Manager owns the product vision, roadmap, and works cross-functionally with engineering, design, and business.
Core skills: Product Strategy, User Research (surveys, interviews, usability tests), Data Analysis (SQL basics, Mixpanel/Amplitude), Roadmapping (Jira, Notion), Stakeholder Management, Agile/Scrum ceremonies.
Nice-to-have: SQL for self-service analytics, Figma/UX basics, A/B Testing, Go-to-market strategy.
Certifications: CSPO (Certified Scrum Product Owner), Google Project Management (Coursera), Product School PM Certificate.
Time to ready (for APM roles): 3-6 months of preparation + strong communication skills.
Salary (India fresher): ₹6-14 LPA. Mid: ₹18-40 LPA. Senior: ₹45-100+ LPA.
Entry point: Associate Product Manager (APM) programs at Google, Microsoft, Swiggy, Razorpay, Atlassian — highly competitive.
Tip: Build case studies. Document product teardowns (Spotify, Swiggy, Notion). Contribute to open source as PM.
""",
    },

    # ── UI/UX Design ─────────────────────────────────────────────────────────
    {
        "id": "uiux_overview",
        "category": "career_path",
        "tags": ["UI/UX designer", "design", "figma", "user experience", "career"],
        "text": """
UI/UX Designer Career Overview
UI/UX Designers create intuitive, beautiful digital experiences.
Core skills: Figma (primary industry tool), User Research methods, Wireframing and prototyping, Design Systems, Accessibility (WCAG), Visual Design principles (typography, color, spacing).
Nice-to-have: HTML/CSS (developers appreciate designer who can code), Motion Design (After Effects, Framer), Usability Testing, Adobe XD.
Certifications: Google UX Design Certificate (Coursera, 6 months, highly recommended), NN/g UX Certification, Adobe Certified Expert.
Time to ready: 3-6 months.
Salary (India fresher): ₹3-7 LPA. Mid: ₹9-20 LPA. Senior: ₹22-50+ LPA.
Portfolio is everything — Behance, Dribbble, and a personal portfolio site are essential.
Companies: Product companies, design agencies, startups, big tech (all need UX).
""",
    },

    # ── Certifications Guide ──────────────────────────────────────────────────
    {
        "id": "top_certifications",
        "category": "certifications",
        "tags": ["certifications", "courses", "learning", "career boost"],
        "text": """
Top Certifications for Tech Students in 2024-25
Free / Low Cost:
  - Google Data Analytics (Coursera, ~6 months) — great for data roles
  - Google UX Design (Coursera, ~6 months) — best intro to UX
  - IBM Data Science Professional Certificate (Coursera) — comprehensive DS
  - Meta Frontend Developer (Coursera) — React and full stack
  - AWS Cloud Practitioner (free prep, ~$100 exam) — cloud fundamentals
  - Microsoft Azure Fundamentals AZ-900 — cloud basics
  - CompTIA Security+ — cybersecurity entry certification
  - CKA (Kubernetes Administrator) — DevOps/Cloud

High Value Paid:
  - AWS Solutions Architect Associate ($300 exam) — cloud engineers
  - AWS Machine Learning Specialty — AI/ML on cloud
  - Google Professional Cloud Architect / ML Engineer — GCP roles
  - Certified Ethical Hacker (CEH) — cybersecurity
  - OSCP (Offensive Security Certified Professional) — penetration testing
  - CSPO (Certified Scrum Product Owner) — product management

Free Learning Platforms:
  - Coursera (financial aid available for free)
  - edX (audit for free)
  - freeCodeCamp (completely free)
  - The Odin Project (completely free, web dev)
  - fast.ai (free, ML/DL)
  - Kaggle Learn (free, data science)
  - CS50 by Harvard (free on edX)
  - NPTEL (free, IIT courses, eligible for proctored exams)
""",
    },

    # ── Interview Prep ────────────────────────────────────────────────────────
    {
        "id": "interview_prep",
        "category": "interview",
        "tags": ["interview", "preparation", "DSA", "coding", "system design"],
        "text": """
Technical Interview Preparation Guide
Data Structures & Algorithms (DSA):
  - Study Arrays, Strings, Linked Lists, Stacks, Queues, Trees, Graphs, Heaps, DP
  - Practice on LeetCode (start with Easy, then Medium), NeetCode.io roadmap is excellent
  - Target: 150-200 problems before interviews at product companies
  - Recommended: Striver's A-Z DSA Sheet (free, Tamil Nadu engineer who cracked Google)

System Design (for 2+ years or senior roles):
  - Learn: Load Balancers, Databases (SQL vs NoSQL), Caching (Redis), Message Queues (Kafka), CDNs, Microservices
  - Resources: System Design Primer (GitHub, free), ByteByteGo (paid but excellent), Grokking System Design (Educative)

Behavioral / HR:
  - Use STAR method (Situation, Task, Action, Result) for all situational questions
  - Common: "Tell me about yourself", "Describe a challenge you solved", "Why this company?"

Resume Tips:
  - Use bullet points with impact metrics: "Improved API response time by 40% by implementing Redis caching"
  - Keep to 1 page for freshers. Use ATS-friendly templates (simple formatting, no tables in header)
  - Include: Skills, Projects (with GitHub links), Education, Certifications, Achievements (hackathons, open source)
""",
    },

    # ── Placement Strategy ────────────────────────────────────────────────────
    {
        "id": "placement_strategy",
        "category": "career_strategy",
        "tags": ["placement", "jobs", "internship", "off-campus", "LinkedIn"],
        "text": """
Job Placement Strategy for Students
On-Campus (College Placements):
  - Most colleges invite TCS, Infosys, Wipro, Cognizant, Capgemini for mass hiring
  - Service companies hire for aptitude + coding basics (not DSA heavy)
  - For product company PPOs: intern at startups, participate in coding competitions

Off-Campus Strategy:
  1. LinkedIn: Connect with recruiters and engineers at target companies. Post about your projects. Apply to jobs directly via LinkedIn Easy Apply.
  2. AngelList (Wellfound): Best for startup jobs. Many don't require referrals.
  3. Internshala: Good for internships to build experience
  4. LeetCode Jobs / HackerEarth / Unstop: Hiring challenges
  5. Referrals: The fastest path. Build genuine connections with alumni from your college who are at target companies.

Portfolio Building:
  - Host projects on GitHub with well-written READMEs
  - Deploy them (Vercel, Netlify, Render are free for small apps)
  - Write about them on LinkedIn or Medium to build visibility
  - Contribute to open source (good first issue labels on GitHub)

Timeline (typical):
  - 6 months before target: Fix resume, start project building
  - 3 months before: Apply actively, do mock interviews
  - 1 month before: Focus only on interview prep, reduce new learning
""",
    },

    # ── Project Ideas ─────────────────────────────────────────────────────────
    {
        "id": "project_ideas_ai",
        "category": "projects",
        "tags": ["projects", "AI", "machine learning", "portfolio", "build"],
        "text": """
Portfolio Project Ideas — AI/ML
Beginner:
  1. Movie/Book Recommendation System — collaborative filtering + content-based filtering (Pandas + Scikit-learn)
  2. Spam Email Classifier — NLP with TF-IDF + Naive Bayes (scikit-learn, 85%+ accuracy target)
  3. House Price Predictor — regression with feature engineering (Boston/Ames dataset on Kaggle)

Intermediate:
  4. Sentiment Analysis Dashboard — fine-tune BERT on product reviews, build a Streamlit UI
  5. Image Classification API — train a CNN in PyTorch, serve via FastAPI, dockerize
  6. Stock Price Forecasting — LSTM + technical indicators (yfinance for data)

Advanced / Portfolio-Worthy:
  7. RAG-Powered Chatbot — LangChain + Pinecone/ChromaDB + OpenAI/Llama, with a web UI
  8. Multi-modal AI App — combine image analysis + text generation (CLIP + LLM)
  9. MLOps Pipeline — train model → track with MLflow → serve with FastAPI → monitor drift
  10. AI Resume Screener — parse PDFs, extract skills, rank candidates against JD using embeddings
""",
    },
    {
        "id": "project_ideas_web",
        "category": "projects",
        "tags": ["projects", "web development", "full stack", "portfolio", "build"],
        "text": """
Portfolio Project Ideas — Full Stack / Web
Beginner:
  1. Personal Portfolio — React + Tailwind, animated sections, contact form with EmailJS
  2. Todo/Task Manager — React + LocalStorage or a backend with Node + MongoDB

Intermediate:
  3. Blog Platform — Next.js + PostgreSQL + Prisma + Auth (NextAuth), Markdown editor
  4. Real-Time Chat App — Socket.io + Express + React, with rooms and message history
  5. Job Board — Full CRUD, filter by category, user auth, company dashboard

Advanced:
  6. SaaS Starter Kit — Auth, Stripe subscriptions, team workspaces, role-based access (Next.js + tRPC)
  7. E-Commerce App — Product listing, cart, Stripe Checkout, order tracking, admin dashboard
  8. Collaborative Whiteboard — WebSockets + Canvas API + React, multi-user real-time

Tips:
  - Every project needs: clean README, live demo link, feature GIFs/screenshots, clear code structure
  - Add a feature flag system, dark mode toggle, or i18n to impress interviewers with product thinking
""",
    },

    # ── Common Questions ─────────────────────────────────────────────────────
    {
        "id": "cgpa_matters",
        "category": "faq",
        "tags": ["CGPA", "grades", "marks", "GPA", "does CGPA matter"],
        "text": """
Does CGPA / Marks Matter?
Short answer: It depends on the company type, but skills and projects matter more for top product companies.

Service companies (TCS, Infosys, Wipro, Cognizant):
  - Minimum CGPA cutoffs are common: usually 6.0-7.5 depending on tier
  - Aptitude tests, verbal reasoning, and basic coding are tested
  - CGPA matters here because volume hiring uses it as a filter

Product companies (Google, Microsoft, Amazon, startups):
  - CGPA is rarely the deciding factor
  - Strong DSA skills, good projects, internship experience matter far more
  - Many engineers at top companies had average CGPAs but stellar projects and preparation

What to do if your CGPA is low:
  - Build a strong GitHub portfolio with high-quality projects
  - Participate in competitive programming (Codeforces, LeetCode) and get ranked
  - Contribute to open source (shows collaboration and code quality)
  - Get an internship (even unpaid initially) and convert it to a PPO
  - Network on LinkedIn, get referrals — many companies don't run CGPA filters for referrals
""",
    },
    {
        "id": "switching_careers",
        "category": "faq",
        "tags": ["career switch", "non-CS", "mechanical", "civil", "change field"],
        "text": """
Career Switching to Tech from Non-CS Background
Many successful engineers switched from Mechanical, Civil, EEE, ECE, or non-engineering backgrounds.

Is it possible? Absolutely yes.
- 30-40% of software engineers in India did NOT study CS
- Bootcamps, self-learning, and projects are your resume

Timeline for a non-CS student to become job-ready:
  - Web Development: 6-9 months intensive self-study
  - Data Science / ML: 9-12 months
  - DevOps / Cloud: 8-12 months

What works:
  1. Pick ONE track and go deep (don't spread across too many languages)
  2. Build 3-5 strong projects and deploy them
  3. Complete a recognized online certification (Coursera, edX)
  4. Apply to startups and service companies first — get experience, then transition to product
  5. Prepare for aptitude + coding tests (service companies don't care about your branch)

Advantage you have: Problem-solving mindset from engineering, and motivation from the outside — use it.
""",
    },
    {
        "id": "open_source_guide",
        "category": "career_strategy",
        "tags": ["open source", "GitHub", "contribute", "GSoC", "portfolio"],
        "text": """
How to Contribute to Open Source
Open source contributions are one of the best resume differentiators.

Getting Started:
  1. Find projects via: GitHub's "good first issue" filter, goodfirstissue.dev, up-for-grabs.net
  2. Start with documentation fixes or test additions — smaller, less intimidating
  3. Read the CONTRIBUTING.md before submitting any PR

Major Programs to Apply For:
  - GSoC (Google Summer of Code): Stipend up to $3000+. Apply in February-March. Highly competitive but prestigious.
  - MLH Fellowship: Paid fellowship with open source contribution for 12 weeks
  - LFX Mentorship: Linux Foundation projects, paid
  - GirlScript Summer of Code (GSSoC): India-focused, good for beginners

What Counts as a Good Contribution:
  - Fix a real bug
  - Add a feature the community requested
  - Improve test coverage
  - Translate documentation
  - Refactor/optimize existing code with benchmarks

Impact on Career:
  - Proves you can read and understand real-world codebases
  - Shows collaboration and communication skills
  - Some companies (especially open-source ones) weigh this very heavily
""",
    },
    {
        "id": "remote_work_freelancing",
        "category": "career_strategy",
        "tags": ["freelancing", "remote work", "Fiverr", "Upwork", "side income"],
        "text": """
Freelancing and Remote Work for Students
Best Platforms to Start:
  - Toptal: High quality, rigorous screening, premium rates ($60-200/hr)
  - Upwork: Large marketplace, good for building profile. Start with competitive bids.
  - Fiverr: Good for productized services (logo design, simple websites, data analysis scripts)
  - LinkedIn: Direct B2B outreach to small businesses needing web development
  - Contra: New platform, no platform fees, good for developers

Skills in Demand for Freelancing (2024-25):
  - Web development (React, Next.js)
  - AI/ML model development and consulting
  - Data scraping and automation (Python)
  - No-code/low-code development (Bubble, Webflow)
  - API integrations
  - Mobile app development (Flutter, React Native)

How to Get First Client:
  1. Create a professional profile with portfolio links
  2. Price yourself 20-30% below market rate initially to get reviews
  3. Apply to 10-15 jobs per day on Upwork when starting
  4. Deliver exceptional quality and ask for a review after completion
  5. Specialize in a niche (e.g., "React developer for SaaS startups")

Earning Potential for Students: ₹20,000 - ₹1,00,000+/month depending on skills and time invested
""",
    },
    {
        "id": "hackathons_competitions",
        "category": "career_strategy",
        "tags": ["hackathon", "competitions", "prizes", "coding contest", "placement boost"],
        "text": """
Hackathons and Coding Competitions — Career Boosters
Why They Matter:
  - Many product companies shortlist hackathon winners for interviews (bypassing normal filters)
  - Demonstrate problem-solving under pressure, teamwork, product thinking
  - Prizes: Cash, internship offers, job offers, mentorship, cloud credits

Top Hackathons in India:
  - Smart India Hackathon (SIH) — Government sponsored, massive scale, great for tier 2-3 college students
  - HackerEarth Hackathons — Multiple per year, online, various tech themes
  - Devfolio Hackathons — Curated community, many prize pools
  - Unstop (formerly Dare2Compete) — Largest platform for competitions in India
  - IIT/IIM-organized events: Shaastra, Techfest, E-Summit hackathons
  - Microsoft Imagine Cup — Global, prestigious, funded if you reach finals
  - Google Hash Code / Code Jam (competitive programming)

International:
  - MLH (Major League Hacking) — 200+ hackathons per year, beginner-friendly
  - HuggingFace Hackathons — AI/ML focused, great networking

Tips to Win:
  1. Solve a real problem, not just a tech demo
  2. Have a working MVP — judges prefer working simple over broken complex
  3. Practice your pitch: 3-minute demo videos work best
  4. Build with APIs and tools quickly (don't reinvent the wheel)
""",
    },
    {
        "id": "general_advice",
        "category": "motivation",
        "tags": ["motivation", "advice", "productivity", "student life", "study tips"],
        "text": """
General Career & Productivity Advice for Students
Study Techniques:
  - Pomodoro Technique: 25 min focused work, 5 min break. Use Forest app or Pomofocus.io
  - Active recall > passive reading. Close the book and test yourself.
  - Feynman Technique: Explain concepts as if teaching a 10-year-old to solidify understanding
  - Spaced repetition: Use Anki for memorizing concepts, algorithms, or syntax

Consistency > Intensity:
  - 1-2 hours daily for 6 months > 10 hours for 2 weeks then stopping
  - Build a habit tracker. Don't break the chain (Jerry Seinfeld method)
  - Find an accountability partner or join study communities (Discord servers: Theo's T3, dev.to, Hashnode)

Managing Burnout:
  - Take Sunday off completely — rest improves retention
  - Exercise, sleep 7-8 hours. Brain learns during sleep (memory consolidation)
  - It's okay to feel overwhelmed. Everyone does. The key is to show up tomorrow.

Mindset:
  - Comparison is the thief of joy. Everyone is on a different timeline.
  - Your CGPA or college tier does NOT determine your career ceiling
  - Your daily habits and the skills you build do
  - Reject the imposter syndrome — every expert was once a beginner

Resources to Stay Motivated:
  - YouTube: Fireship, Theo - t3.gg, The Primeagen, TwoSetViolin (for fun breaks)
  - Podcasts: Lex Fridman, My First Million, Cortex
  - Books: "Atomic Habits" by James Clear, "Deep Work" by Cal Newport, "The Pragmatic Programmer"
""",
    },
]


# ─────────────────────────────────────────────────────────────────────────────
# Simple TF-IDF-style Retrieval
# ─────────────────────────────────────────────────────────────────────────────

def _tokenize(text: str) -> List[str]:
    """Lowercase and split text into word tokens."""
    text = text.lower()
    tokens = re.findall(r"[a-z0-9]+", text)
    return tokens


def _score_document(query_tokens: List[str], doc: Dict[str, Any]) -> float:
    """
    Score a document against a query.
    Combines tag matching (high weight) with text frequency matching.
    """
    score = 0.0

    # Tag matching — exact tag hit = high weight
    query_str = " ".join(query_tokens)
    for tag in doc.get("tags", []):
        tag_lower = tag.lower()
        # Check if any tag word appears in query
        for tword in tag_lower.split():
            if tword in query_tokens:
                score += 5.0  # high weight for tag match
        # Partial tag match in full query string
        if any(qt in tag_lower for qt in query_tokens if len(qt) > 3):
            score += 2.0

    # Text term frequency
    doc_tokens = _tokenize(doc.get("text", ""))
    doc_len = max(len(doc_tokens), 1)
    doc_freq: Dict[str, int] = {}
    for t in doc_tokens:
        doc_freq[t] = doc_freq.get(t, 0) + 1

    for qt in query_tokens:
        if len(qt) < 3:
            continue
        tf = doc_freq.get(qt, 0) / doc_len
        if tf > 0:
            # IDF approximation — rarer terms get higher weight
            doc_count = sum(1 for d in KNOWLEDGE_BASE if qt in " ".join(_tokenize(d.get("text", ""))))
            idf = math.log((len(KNOWLEDGE_BASE) + 1) / (doc_count + 1)) + 1
            score += tf * idf

    return score


def retrieve_context(query: str, top_k: int = 4) -> List[Dict[str, Any]]:
    """
    Retrieve the top_k most relevant knowledge chunks for a query.
    Returns list of dicts: { id, category, tags, text, score }
    """
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []

    scored = []
    for doc in KNOWLEDGE_BASE:
        s = _score_document(query_tokens, doc)
        if s > 0:
            scored.append({**doc, "score": s})

    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored[:top_k]


def retrieve_context_text(query: str, top_k: int = 4, max_chars: int = 4000) -> str:
    """
    Convenience function: retrieve context and return as a single formatted string.
    Caps total output at max_chars to stay within LLM context limits.
    """
    chunks = retrieve_context(query, top_k=top_k)
    if not chunks:
        return ""

    parts = []
    total = 0
    for chunk in chunks:
        text = f"[Source: {chunk['category'].upper()} — {', '.join(chunk['tags'][:3])}]\n{chunk['text'].strip()}"
        if total + len(text) > max_chars:
            break
        parts.append(text)
        total += len(text)

    return "\n\n---\n\n".join(parts)
