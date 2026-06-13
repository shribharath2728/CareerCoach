"""
SkillLens Reasoning Agent
=========================
Multi-step reasoning pipeline for career analysis.
Steps: Profile → Goal → Knowledge → Gap Analysis → Reasoning → Recommendation → Explanation

Uses the unified AI provider (Groq → Gemini → Claude waterfall) via ai_provider.chat_complete().
RAG: Uses rag_knowledge.retrieve_context_text() to inject relevant career knowledge
dynamically into the agent's system prompt based on the user's query.
"""
import json
import os
import re
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.core.ai_provider import chat_complete, DEFAULT_GROQ_MODEL
from app.services.rag_knowledge import retrieve_context_text

# ─────────────────────────────────────────────────────────────────────────────
# Career knowledge base (static, augmented by LLM)
# ─────────────────────────────────────────────────────────────────────────────

CAREER_SKILL_MAP: Dict[str, Dict[str, Any]] = {
    "AI Engineer": {
        "required_skills": ["Python", "Machine Learning", "Deep Learning", "TensorFlow/PyTorch", "MLOps", "Vector Databases", "LLMs", "Data Structures"],
        "nice_to_have": ["Docker", "Kubernetes", "Cloud (AWS/GCP/Azure)", "SQL", "Statistics"],
        "certifications": ["AWS ML Specialty", "Google Professional ML Engineer", "DeepLearning.AI courses"],
        "salary_range": {"fresher": "₹6-12 LPA", "mid": "₹15-35 LPA", "senior": "₹40-80+ LPA"},
        "avg_time_to_ready": "8-12 months",
    },
    "Data Scientist": {
        "required_skills": ["Python", "Statistics", "Machine Learning", "Data Visualization", "SQL", "Pandas", "Scikit-learn"],
        "nice_to_have": ["R", "Spark", "Tableau", "Deep Learning", "A/B Testing"],
        "certifications": ["IBM Data Science Professional", "Google Data Analytics", "Coursera ML Specialization"],
        "salary_range": {"fresher": "₹5-10 LPA", "mid": "₹12-30 LPA", "senior": "₹35-70+ LPA"},
        "avg_time_to_ready": "6-10 months",
    },
    "Full Stack Developer": {
        "required_skills": ["HTML", "CSS", "JavaScript", "React/Vue/Angular", "Node.js", "SQL/NoSQL", "REST APIs", "Git"],
        "nice_to_have": ["TypeScript", "Docker", "CI/CD", "GraphQL", "AWS", "Testing"],
        "certifications": ["Meta Frontend Certificate", "AWS Developer Associate", "MongoDB Certified Developer"],
        "salary_range": {"fresher": "₹4-8 LPA", "mid": "₹10-22 LPA", "senior": "₹25-55+ LPA"},
        "avg_time_to_ready": "4-8 months",
    },
    "Cloud Engineer": {
        "required_skills": ["Linux", "Networking", "AWS/Azure/GCP", "Terraform/IaC", "Docker", "Kubernetes", "Python/Bash"],
        "nice_to_have": ["CI/CD", "Security", "Monitoring (Prometheus)", "Serverless"],
        "certifications": ["AWS Solutions Architect", "Azure Administrator", "GCP Professional Cloud Architect"],
        "salary_range": {"fresher": "₹5-10 LPA", "mid": "₹14-28 LPA", "senior": "₹30-65+ LPA"},
        "avg_time_to_ready": "6-10 months",
    },
    "Cybersecurity Analyst": {
        "required_skills": ["Networking", "Linux", "Python", "SIEM Tools", "Penetration Testing", "Risk Assessment"],
        "nice_to_have": ["Ethical Hacking", "Forensics", "Cloud Security", "Compliance"],
        "certifications": ["CompTIA Security+", "CEH", "CISSP", "OSCP"],
        "salary_range": {"fresher": "₹4-9 LPA", "mid": "₹12-25 LPA", "senior": "₹28-60+ LPA"},
        "avg_time_to_ready": "6-12 months",
    },
    "DevOps Engineer": {
        "required_skills": ["Linux", "Docker", "Kubernetes", "CI/CD (Jenkins/GitLab)", "Python/Bash", "Git", "Monitoring"],
        "nice_to_have": ["Terraform", "Ansible", "AWS/Azure", "Go", "Service Mesh"],
        "certifications": ["Docker Certified Associate", "Kubernetes CKA", "AWS DevOps Professional"],
        "salary_range": {"fresher": "₹5-10 LPA", "mid": "₹13-28 LPA", "senior": "₹30-65+ LPA"},
        "avg_time_to_ready": "5-9 months",
    },
    "Product Manager": {
        "required_skills": ["Product Strategy", "User Research", "Data Analysis", "Roadmapping", "Stakeholder Management", "Agile"],
        "nice_to_have": ["SQL", "Figma/UX", "A/B Testing", "Go-to-market"],
        "certifications": ["CSPO", "Product School", "Google PM Certificate"],
        "salary_range": {"fresher": "₹6-14 LPA", "mid": "₹18-40 LPA", "senior": "₹45-100+ LPA"},
        "avg_time_to_ready": "3-6 months",
    },
    "UI/UX Designer": {
        "required_skills": ["Figma", "User Research", "Wireframing", "Prototyping", "Design Systems", "Accessibility"],
        "nice_to_have": ["HTML/CSS", "Motion Design", "Usability Testing", "Adobe XD"],
        "certifications": ["Google UX Design Certificate", "NN/g UX Certification", "Adobe Certified Expert"],
        "salary_range": {"fresher": "₹3-7 LPA", "mid": "₹9-20 LPA", "senior": "₹22-50+ LPA"},
        "avg_time_to_ready": "3-6 months",
    },
}


def _client(model: Optional[str] = None) -> tuple:
    """Legacy shim — returns (None, model_id) so existing callers compile.
    Actual API calls go through chat_complete() in each function below."""
    from app.core.ai_provider import resolve_model
    provider, model_id = resolve_model(model)
    return None, model_id


def _safe_json(text: str) -> Any:
    text = text.strip()
    # Strip markdown fences
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        m = re.search(r"\{[\s\S]*\}", text)
        if m:
            try:
                return json.loads(m.group(0))
            except Exception:
                pass
        m2 = re.search(r"\[[\s\S]*\]", text)
        if m2:
            try:
                return json.loads(m2.group(0))
            except Exception:
                pass
    return {}


# ─────────────────────────────────────────────────────────────────────────────
# Core reasoning functions
# ─────────────────────────────────────────────────────────────────────────────

def analyze_profile(profile: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
    """Step 2: Analyze user profile — strengths, weaknesses, industry readiness."""
    _, model_id = _client(model)
    prompt = f"""
You are an expert career analyst. Analyze this student profile deeply:

Profile:
{json.dumps(profile, indent=2)}

Return ONLY valid JSON with this exact structure:
{{
  "skill_level": "beginner|intermediate|advanced",
  "strengths": ["list of 3-5 genuine strengths based on their skills/projects"],
  "weaknesses": ["list of 3-5 skill gaps or areas needing improvement"],
  "industry_readiness_score": <integer 0-100>,
  "readiness_level": "not_ready|developing|nearly_ready|ready",
  "analysis_summary": "2-3 sentences explaining the overall assessment",
  "key_advantage": "Their biggest competitive advantage",
  "urgent_improvement": "The single most important thing to improve"
}}
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a precise career analyst. Return ONLY valid JSON.",
            model_hint=model_id,
            temperature=0.3,
            max_tokens=2000,
        )
        return _safe_json(raw)
    except Exception:
        return {
            "skill_level": "intermediate",
            "strengths": profile.get("skills", [])[:3],
            "weaknesses": [],
            "industry_readiness_score": 50,
            "readiness_level": "developing",
            "analysis_summary": "Profile analysis completed.",
            "key_advantage": "Motivation to learn",
            "urgent_improvement": "Build more projects",
        }


def detect_skill_gaps(profile: Dict[str, Any], career_goal: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Step 3: Gap Detection — compare current skills vs career requirements."""
    _, model_id = _client(model)

    # Get static knowledge base data for the career goal
    career_data = CAREER_SKILL_MAP.get(career_goal, {})
    required_skills = career_data.get("required_skills", [])
    current_skills = [s.strip().lower() for s in profile.get("skills", [])]

    # Quick static gap detection
    present_skills = []
    missing_skills = []
    for skill in required_skills:
        if any(skill.lower() in cs or cs in skill.lower() for cs in current_skills):
            present_skills.append(skill)
        else:
            missing_skills.append(skill)

    match_percentage = round((len(present_skills) / max(len(required_skills), 1)) * 100)

    prompt = f"""
You are a career gap analyst. The user wants to become a {career_goal}.

User's current skills: {profile.get("skills", [])}
User's projects: {profile.get("projects", [])}
User's certifications: {profile.get("certifications", [])}
Required skills for {career_goal}: {required_skills}
Static gap analysis: Present={present_skills}, Missing={missing_skills}

Provide a detailed gap analysis. Return ONLY valid JSON:
{{
  "career_goal": "{career_goal}",
  "current_skills_present": {json.dumps(present_skills)},
  "missing_critical_skills": ["list of most critical missing skills, ordered by priority"],
  "missing_nice_to_have": ["nice to have skills they're missing"],
  "match_percentage": {match_percentage},
  "priority_learning_order": ["skill1 → reason", "skill2 → reason", "skill3 → reason"],
  "estimated_preparation_time": "X months based on their current level",
  "quick_wins": ["skills they can learn quickly in 1-2 weeks"],
  "gap_summary": "2 sentence summary of the gap situation"
}}
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a precise skill gap analyst. Return ONLY valid JSON.",
            model_hint=model_id,
            temperature=0.2,
            max_tokens=2000,
        )
        result = _safe_json(raw)
        result.setdefault("current_skills_present", present_skills)
        result.setdefault("missing_critical_skills", missing_skills)
        result.setdefault("match_percentage", match_percentage)
        result.setdefault("career_goal", career_goal)
        return result
    except Exception:
        return {
            "career_goal": career_goal,
            "current_skills_present": present_skills,
            "missing_critical_skills": missing_skills,
            "missing_nice_to_have": career_data.get("nice_to_have", []),
            "match_percentage": match_percentage,
            "priority_learning_order": [f"Learn {s}" for s in missing_skills[:3]],
            "estimated_preparation_time": career_data.get("avg_time_to_ready", "6-12 months"),
            "quick_wins": [],
            "gap_summary": f"You have {len(present_skills)}/{len(required_skills)} required skills for {career_goal}.",
        }


def generate_roadmap(profile: Dict[str, Any], career_goal: str, skill_gaps: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
    """Step 4: Generate 30/90/180 day roadmap with projects and certifications."""
    _, model_id = _client(model)
    career_data = CAREER_SKILL_MAP.get(career_goal, {})

    prompt = f"""
You are a career roadmap architect. Create a highly detailed, comprehensive personalized learning roadmap.

Student Profile:
- Name: {profile.get("name", "Student")}
- CGPA: {profile.get("cgpa", "N/A")}
- Year: {profile.get("year", "N/A")}
- Current Skills: {profile.get("skills", [])}
- Career Goal: {career_goal}
- Missing Skills: {skill_gaps.get("missing_critical_skills", [])}
- Certifications already done: {profile.get("certifications", [])}

CRITICAL DATA REQUIREMENT:
Generate extensive, granular data. Each phase must contain at least 5-6 focus skills, 5-6 daily tasks with descriptions, and 4-5 specific online course/platform recommendations (naming the exact platform and course title). Provide at least 4 certifications and 4-5 rich project recommendations with complete, detailed descriptions.

Return ONLY valid JSON:
{{
  "roadmap_title": "Comprehensive Path to {career_goal}",
  "phase_30_days": {{
    "theme": "Foundation Building & Core Basics",
    "focus_skills": ["detailed skill 1", "detailed skill 2", "detailed skill 3", "detailed skill 4", "detailed skill 5"],
    "daily_tasks": [
      "Task 1: specific daily learning and practice routine",
      "Task 2: practical exercises and labs",
      "Task 3: concept building",
      "Task 4: code challenge practice",
      "Task 5: documentation reading"
    ],
    "milestone": "What concrete skill achievements they will show by day 30",
    "resources": [
      "Udemy: [Exact Course Name]",
      "Coursera: [Exact Specialization/Course Name]",
      "YouTube: [Channel/Series name]",
      "Documentation: [Official portal links/names]"
    ],
    "mini_project": "Small project description to build in this phase"
  }},
  "phase_90_days": {{
    "theme": "Core Competency & Interactive Applications",
    "focus_skills": ["detailed skill 1", "detailed skill 2", "detailed skill 3", "detailed skill 4", "detailed skill 5"],
    "daily_tasks": [
      "Task 1: specific daily learning and practice routine",
      "Task 2: intermediate coding challenges",
      "Task 3: API integration practice",
      "Task 4: database modeling design",
      "Task 5: unit testing setup"
    ],
    "milestone": "What concrete skill achievements they will show by day 90",
    "resources": [
      "Udemy: [Exact Course Name]",
      "Coursera: [Exact Specialization/Course Name]",
      "YouTube: [Channel/Series name]",
      "Interactive Platform: [Platform details]"
    ],
    "project": "Medium project description demonstrating multiple complex skills"
  }},
  "phase_180_days": {{
    "theme": "Job Readiness & Portfolio Capstone",
    "focus_skills": ["detailed skill 1", "detailed skill 2", "detailed skill 3", "detailed skill 4", "detailed skill 5"],
    "daily_tasks": [
      "Task 1: specific daily learning and practice routine",
      "Task 2: system design implementation",
      "Task 3: deployment and CI/CD setup",
      "Task 4: code optimization/refactoring",
      "Task 5: mock interview prep"
    ],
    "milestone": "What concrete skill achievements they will show by day 180",
    "resources": [
      "Udemy: [Exact Advanced Course Name]",
      "Coursera: [Exact Advanced Specialization Name]",
      "Books: [Specific textbook recommendation]",
      "Portals: [Advanced prep guides]"
    ],
    "capstone_project": "Portfolio-worthy production grade capstone project description"
  }},
  "certifications": [
    {{"name": "Specific Certification Name 1", "platform": "Coursera/Udemy/AWS/etc", "duration": "X weeks", "priority": "high"}},
    {{"name": "Specific Certification Name 2", "platform": "Coursera/Udemy/Google/etc", "duration": "Y weeks", "priority": "medium"}},
    {{"name": "Specific Certification Name 3", "platform": "Coursera/Udemy/etc", "duration": "Z weeks", "priority": "high"}},
    {{"name": "Specific Certification Name 4", "platform": "Coursera/Udemy/etc", "duration": "W weeks", "priority": "medium"}}
  ],
  "project_recommendations": [
    {{"name": "Project Name 1", "description": "Highly detailed project description of what to build and why", "skills_demonstrated": ["skill1", "skill2"], "difficulty": "beginner", "time_to_build": "X weeks"}},
    {{"name": "Project Name 2", "description": "Highly detailed project description of what to build and why", "skills_demonstrated": ["skill3", "skill4"], "difficulty": "intermediate", "time_to_build": "Y weeks"}},
    {{"name": "Project Name 3", "description": "Highly detailed project description of what to build and why", "skills_demonstrated": ["skill5", "skill6"], "difficulty": "advanced", "time_to_build": "Z weeks"}},
    {{"name": "Project Name 4", "description": "Highly detailed project description of what to build and why", "skills_demonstrated": ["skill7", "skill8"], "difficulty": "advanced", "time_to_build": "W weeks"}}
  ],
  "job_titles_to_target": ["Specific Title 1", "Specific Title 2", "Specific Title 3", "Specific Title 4"],
  "expected_salary": "{career_data.get('salary_range', {}).get('fresher', 'Competitive')}"
}}
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert career roadmap creator. Return ONLY valid JSON.",
            model_hint=model_id,
            temperature=0.4,
            max_tokens=2000,
        )
        return _safe_json(raw)
    except Exception:
        return {
            "roadmap_title": f"Your Path to {career_goal}",
            "phase_30_days": {"theme": "Foundation", "focus_skills": skill_gaps.get("missing_critical_skills", [])[:2], "milestone": "Learn fundamentals", "mini_project": "Starter project"},
            "phase_90_days": {"theme": "Core Competency", "focus_skills": skill_gaps.get("missing_critical_skills", [])[2:4], "milestone": "Build core projects", "project": "Portfolio project"},
            "phase_180_days": {"theme": "Job Readiness", "focus_skills": ["Advanced topics"], "milestone": "Ready to apply", "capstone_project": "Capstone project"},
            "certifications": [{"name": c, "platform": "Online", "duration": "4 weeks", "priority": "high"} for c in career_data.get("certifications", [])[:3]],
            "project_recommendations": [],
        }


def calculate_confidence_score(profile: Dict[str, Any], career_goal: str, skill_gaps: Dict[str, Any], profile_analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Step 6: Calculate career match confidence score with detailed reasoning."""
    career_data = CAREER_SKILL_MAP.get(career_goal, {})
    required = len(career_data.get("required_skills", []))
    present = len(skill_gaps.get("current_skills_present", []))

    # Component scores
    skill_score = round((present / max(required, 1)) * 40)  # 40% weight
    project_score = min(len(profile.get("projects", [])) * 8, 20)  # 20% weight
    cert_score = min(len(profile.get("certifications", [])) * 5, 15)  # 15% weight
    readiness_score = round(profile_analysis.get("industry_readiness_score", 50) * 0.25)  # 25% weight
    total_score = min(skill_score + project_score + cert_score + readiness_score, 100)

    reasons = []
    if skill_score > 25:
        reasons.append(f"Strong skill foundation ({present}/{required} required skills)")
    elif skill_score > 15:
        reasons.append(f"Moderate skill coverage ({present}/{required} required skills)")
    else:
        reasons.append(f"Skill gaps present — need to learn {required - present} more skills")

    if project_score > 12:
        reasons.append("Impressive project portfolio")
    elif project_score > 5:
        reasons.append("Good project experience — add more complex projects")
    else:
        reasons.append("Build more projects to showcase practical experience")

    if cert_score > 8:
        reasons.append("Good certifications on profile")
    else:
        reasons.append("Adding certifications would boost credibility")

    label = "Excellent Match" if total_score >= 80 else "Good Match" if total_score >= 60 else "Developing" if total_score >= 40 else "Early Stage"
    color = "#10B981" if total_score >= 80 else "#6366F1" if total_score >= 60 else "#F59E0B" if total_score >= 40 else "#EF4444"

    return {
        "overall_score": total_score,
        "label": label,
        "color": color,
        "component_scores": {
            "skills": {"score": skill_score, "max": 40, "label": "Technical Skills"},
            "projects": {"score": project_score, "max": 20, "label": "Project Experience"},
            "certifications": {"score": cert_score, "max": 15, "label": "Certifications"},
            "readiness": {"score": readiness_score, "max": 25, "label": "Industry Readiness"},
        },
        "reasons": reasons,
        "improvement_tip": f"Focus on: {', '.join(skill_gaps.get('missing_critical_skills', ['core skills'])[:2])} to boost your score.",
    }


def generate_reasoning_explanation(profile: Dict[str, Any], career_goal: str, skill_gaps: Dict[str, Any], model: Optional[str] = None) -> List[Dict[str, str]]:
    """Step 5: Generate transparent reasoning chain explaining recommendations using Foundry IQ Layer."""
    from app.services.foundry_iq import foundry_iq
    _, model_id = _client(model)
    return foundry_iq.generate_grounded_reasoning(profile, career_goal, skill_gaps, model_id)


def simulate_career_growth(profile: Dict[str, Any], career_goal: str, hours_per_day: float, months: int, model: Optional[str] = None) -> Dict[str, Any]:
    """Career Simulation Engine — predict career trajectory and generate unified 30/90/180 roadmap."""
    _, model_id = _client(model)
    total_hours = hours_per_day * 30 * months
    career_data = CAREER_SKILL_MAP.get(career_goal, {})

    prompt = f"""
Simulate the career growth of a student studying {hours_per_day} hours/day for {months} months ({total_hours:.0f} total hours).
Combine the Career Simulation trajectory with a highly structured, actionable Learning Roadmap for {career_goal}.

Student Profile:
- Current Skills: {profile.get("skills", [])}
- Current Level: {profile.get("cgpa", "N/A")} CGPA
- Goal: {career_goal}
- Required skills to learn: {career_data.get("required_skills", [])}

Provide a realistic month-by-month simulation and granular roadmap. Return ONLY valid JSON:
{{
  "simulation_summary": "One paragraph overview of the journey",
  "monthly_milestones": [
    {{"month": 1, "skills_gained": [], "project_built": "What they'll build", "readiness_boost": "+X% closer to job ready"}}
  ],
  "final_state": {{
    "skills_gained": ["complete list of new skills"],
    "projects_portfolio": ["project1", "project2"],
    "expected_job_roles": ["role1", "role2", "role3"],
    "salary_range": "Estimated salary with {months} months of preparation",
    "job_readiness": <0-100 integer>,
    "companies_to_target": ["Company 1", "Company 2", "Company 3"]
  }},
  "phase_30_days": {{
    "theme": "Foundation Building & Core Basics",
    "focus_skills": ["detailed skill 1", "detailed skill 2", "detailed skill 3", "detailed skill 4"],
    "daily_tasks": [
      "Task 1: specific daily learning and practice routine",
      "Task 2: practical exercises and labs",
      "Task 3: concept building",
      "Task 4: code challenge practice",
      "Task 5: documentation reading"
    ],
    "milestone": "What concrete skill achievements they will show by day 30"
  }},
  "phase_90_days": {{
    "theme": "Core Competency & Interactive Applications",
    "focus_skills": ["detailed skill 1", "detailed skill 2", "detailed skill 3", "detailed skill 4"],
    "daily_tasks": [
      "Task 1: intermediate coding challenges",
      "Task 2: API integration practice",
      "Task 3: database modeling design",
      "Task 4: unit testing setup",
      "Task 5: small project deployment"
    ],
    "milestone": "What concrete skill achievements they will show by day 90"
  }},
  "phase_180_days": {{
    "theme": "Job Readiness & Portfolio Capstone",
    "focus_skills": ["detailed skill 1", "detailed skill 2", "detailed skill 3", "detailed skill 4"],
    "daily_tasks": [
      "Task 1: system design implementation",
      "Task 2: deployment and CI/CD setup",
      "Task 3: code optimization/refactoring",
      "Task 4: mock interview prep",
      "Task 5: portfolio polishing"
    ],
    "milestone": "What concrete skill achievements they will show by day 180"
  }},
  "certifications": [
    {{"name": "Specific Certification Name 1", "platform": "Coursera/Udemy/AWS/etc", "duration": "X weeks", "priority": "high"}},
    {{"name": "Specific Certification Name 2", "platform": "Coursera/Udemy/Google/etc", "duration": "Y weeks", "priority": "medium"}},
    {{"name": "Specific Certification Name 3", "platform": "Coursera/Udemy/etc", "duration": "Z weeks", "priority": "high"}}
  ],
  "courses_and_modules": [
    {{"name": "Course or Module name", "topics": ["topic 1", "topic 2"], "duration": "Recommended study duration", "difficulty": "Beginner/Intermediate/Advanced"}}
  ],
  "projects_to_build": [
    {{"title": "Project title", "description": "What they'll build, core features & tech stack", "skills_applied": ["skill1", "skill2"], "complexity": "Beginner/Intermediate/Advanced"}}
  ],
  "sources_to_refer": [
    {{"resource": "Resource name / platform (e.g. MDN Web Docs, freeCodeCamp)", "type": "Documentation/YouTube/Online Course/Book", "focus": "What specific skills to reference here", "link_or_platform": "Platform name or URL reference"}}
  ],
  "reasoning": "Why this simulation predicts this outcome — step by step logic",
  "acceleration_tips": ["tip to speed up learning"],
  "risk_factors": ["things that could slow progress"]
}}
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a career trajectory and roadmap simulator. Return ONLY valid JSON.",
            model_hint=model_id,
            temperature=0.4,
            max_tokens=2000,
        )
        return _safe_json(raw)
    except Exception:
        return {
            "simulation_summary": f"Studying {hours_per_day} hours/day for {months} months will significantly improve your {career_goal} readiness.",
            "monthly_milestones": [
                {"month": 1, "skills_gained": career_data.get("required_skills", [])[:2], "project_built": "Starter Project", "readiness_boost": "+15%"},
                {"month": 3, "skills_gained": career_data.get("required_skills", [])[2:4], "project_built": "Intermediate Project", "readiness_boost": "+35%"}
            ],
            "final_state": {
                "skills_gained": career_data.get("required_skills", []),
                "projects_portfolio": ["Portfolio project"],
                "expected_job_roles": [career_goal, f"Junior {career_goal}"],
                "salary_range": career_data.get("salary_range", {}).get("fresher", "Competitive"),
                "job_readiness": min(60 + int(hours_per_day * months * 2), 100),
                "companies_to_target": ["MNCs", "Startups", "Product Companies"],
            },
            "phase_30_days": {
                "theme": "Foundation",
                "focus_skills": career_data.get("required_skills", [])[:3],
                "daily_tasks": ["Learn core syntax", "Write simple scripts", "Read official documentation"],
                "milestone": "Understand fundamentals"
            },
            "phase_90_days": {
                "theme": "Core Competency",
                "focus_skills": career_data.get("required_skills", [])[3:6],
                "daily_tasks": ["Build basic app", "Integrate databases", "Implement core logic"],
                "milestone": "Build intermediate projects"
            },
            "phase_180_days": {
                "theme": "Job Readiness",
                "focus_skills": career_data.get("required_skills", [])[6:],
                "daily_tasks": ["Deploy full stack app", "Optimize queries", "Practice mock interviews"],
                "milestone": "Ready to apply"
            },
            "certifications": [{"name": c, "platform": "Online", "duration": "4 weeks", "priority": "high"} for c in career_data.get("certifications", [])[:3]],
            "courses_and_modules": [
                {"name": f"Complete {career_goal} Path", "topics": career_data.get("required_skills", []), "duration": f"{months} months", "difficulty": "All Levels"}
            ],
            "projects_to_build": [
                {"title": f"End-to-End {career_goal} Project", "description": "A comprehensive portfolio project demonstrating key required skills.", "skills_applied": career_data.get("required_skills", [])[:3], "complexity": "Intermediate"}
            ],
            "sources_to_refer": [
                {"resource": "Official Documentation", "type": "Documentation", "focus": "Core language and framework reference", "link_or_platform": "Web/Docs"}
            ],
            "reasoning": "Based on your study commitment and current skills.",
            "acceleration_tips": ["Build projects while learning"],
            "risk_factors": ["Inconsistent practice"],
        }


def analyze_resume_text(resume_text: str, career_goal: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Resume analysis — extract skills, detect gaps, generate ATS score and improvements."""
    _, model_id = _client(model)
    career_data = CAREER_SKILL_MAP.get(career_goal, {})
    required_skills = career_data.get("required_skills", [])

    prompt = f"""
You are an expert ATS (Applicant Tracking System) analyzer and resume coach.

Analyze this resume for a candidate targeting: {career_goal}
Required skills for this role: {required_skills}

Resume text:
{resume_text[:8000]}

Return ONLY valid JSON:
{{
  "ats_score": <integer 0-100>,
  "extracted_skills": ["all skills found in the resume"],
  "missing_keywords": ["important keywords missing for {career_goal}"],
  "keyword_density": {{"keyword": count}},
  "section_scores": {{
    "contact_info": <0-10>,
    "education": <0-20>,
    "experience": <0-30>,
    "skills": <0-25>,
    "projects": <0-15>
  }},
  "strengths": ["what the resume does well"],
  "improvements": [
    {{"section": "section name", "issue": "specific issue", "fix": "exact fix to apply"}}
  ],
  "missing_sections": ["sections that should be added"],
  "action_verb_quality": "weak|average|strong",
  "quantification_score": <0-10>,
  "overall_verdict": "Summary of the resume quality",
  "rewrite_suggestions": ["specific rewrites for impact statements"]
}}
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert ATS analyzer. Return ONLY valid JSON.",
            model_hint=model_id,
            temperature=0.2,
            max_tokens=2000,
        )
        return _safe_json(raw)
    except Exception:
        return {
            "ats_score": 50,
            "extracted_skills": [],
            "missing_keywords": required_skills[:5],
            "improvements": [{"section": "Skills", "issue": "Missing key skills", "fix": "Add required technical skills"}],
            "overall_verdict": "Resume needs improvement for " + career_goal,
        }


def calculate_job_readiness(profile: Dict[str, Any], career_goal: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Job Readiness Analyzer — multi-dimensional employability score."""
    _, model_id = _client(model)

    prompt = f"""
Calculate a comprehensive Job Readiness Score for this student.

Profile:
{json.dumps(profile, indent=2)}
Career Goal: {career_goal}

Return ONLY valid JSON:
{{
  "resume_score": <0-100>,
  "portfolio_score": <0-100>,
  "linkedin_score": <0-100>,
  "technical_score": <0-100>,
  "communication_score": <0-100>,
  "overall_employability_score": <0-100>,
  "score_breakdown": {{
    "resume": {{"score": 0, "reason": "why this score", "improve": "specific action"}},
    "portfolio": {{"score": 0, "reason": "why", "improve": "specific action"}},
    "linkedin": {{"score": 0, "reason": "why", "improve": "specific action"}},
    "technical": {{"score": 0, "reason": "why", "improve": "specific action"}},
    "communication": {{"score": 0, "reason": "why", "improve": "specific action"}}
  }},
  "hiring_probability": "percentage chance of getting an interview in next 3 months",
  "top_action_items": ["most impactful thing to do this week", "second priority", "third priority"],
  "employer_appeal_level": "low|moderate|good|excellent",
  "readiness_verdict": "One sentence overall assessment"
}}
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You calculate job readiness scores. Return ONLY valid JSON.",
            model_hint=model_id,
            temperature=0.25,
            max_tokens=2000,
        )
        result = _safe_json(raw)
        # Compute overall if not set
        if not result.get("overall_employability_score"):
            scores = [result.get(k, 0) for k in ("resume_score", "portfolio_score", "technical_score")]
            result["overall_employability_score"] = round(sum(scores) / max(len(scores), 1))
        return result
    except Exception:
        return {
            "resume_score": 55,
            "portfolio_score": 40,
            "linkedin_score": 45,
            "technical_score": 60,
            "communication_score": 70,
            "overall_employability_score": 54,
            "hiring_probability": "30%",
            "top_action_items": ["Build a portfolio project", "Update your resume", "Complete LinkedIn profile"],
            "employer_appeal_level": "moderate",
            "readiness_verdict": "You're on track but need to strengthen your portfolio.",
        }


def get_project_mentor_recommendations(profile: Dict[str, Any], career_goal: str, available_hours_per_week: int, model: Optional[str] = None) -> Dict[str, Any]:
    """Project Mentor — recommend projects based on skill level, goal, and time."""
    _, model_id = _client(model)

    prompt = f"""
You are a project mentor. Recommend ideal projects for this student.

Student:
- Skills: {profile.get("skills", [])}
- Career Goal: {career_goal}
- CGPA: {profile.get("cgpa", "N/A")}
- Available time: {available_hours_per_week} hours/week
- Existing Projects: {profile.get("projects", [])}

Return ONLY valid JSON:
{{
  "beginner_projects": [
    {{"name": "", "description": "", "skills_learned": [], "time_weeks": 1, "why_recommended": "", "github_template": "search query"}}
  ],
  "intermediate_projects": [
    {{"name": "", "description": "", "skills_learned": [], "time_weeks": 2, "why_recommended": "", "impact": "how this helps career"}}
  ],
  "advanced_projects": [
    {{"name": "", "description": "", "skills_learned": [], "time_weeks": 4, "why_recommended": "", "interview_talking_point": "how to explain this in interview"}}
  ],
  "capstone_project": {{
    "name": "The single best project for this student",
    "description": "Detailed description",
    "skills_demonstrated": [],
    "estimated_time": "X weeks",
    "why_this_project_is_perfect": "Reasoning"
  }},
  "project_stack_recommendation": "Technology stack to use for all projects",
  "portfolio_strategy": "How to present these projects to employers"
}}
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are a project mentor. Return ONLY valid JSON.",
            model_hint=model_id,
            temperature=0.5,
            max_tokens=2000,
        )
        return _safe_json(raw)
    except Exception:
        return {
            "beginner_projects": [],
            "intermediate_projects": [],
            "advanced_projects": [],
            "capstone_project": {"name": "Full Portfolio App", "description": f"Build a full {career_goal} portfolio project", "skills_demonstrated": [], "estimated_time": "4 weeks"},
            "project_stack_recommendation": "Python + relevant frameworks",
        }


# ─────────────────────────────────────────────────────────────────────────────
# Master orchestrator
# ─────────────────────────────────────────────────────────────────────────────

def run_full_agent_analysis(profile: Dict[str, Any], career_goal: str, model: Optional[str] = None) -> Dict[str, Any]:
    """
    Master pipeline: runs all reasoning steps and returns a structured full analysis.
    Emits reasoning_steps for the Agent Thinking Panel.
    """
    reasoning_steps = []

    # Step 1: Profile Understanding
    reasoning_steps.append({
        "step": 1, "title": "Understanding Your Profile",
        "status": "complete",
        "detail": f"Collected profile for {profile.get('name', 'you')}: {profile.get('year', '')} year {profile.get('branch', '')} student with CGPA {profile.get('cgpa', 'N/A')}."
    })

    # Step 2: Profile Analysis
    reasoning_steps.append({"step": 2, "title": "Analyzing Skills & Experience", "status": "processing", "detail": "Evaluating strengths, weaknesses, and industry readiness..."})
    profile_analysis = analyze_profile(profile, model)
    reasoning_steps[-1]["status"] = "complete"
    reasoning_steps[-1]["detail"] = f"Skill level: {profile_analysis.get('skill_level', 'intermediate')}. Readiness: {profile_analysis.get('industry_readiness_score', 0)}%"

    # Step 3: Gap Detection
    reasoning_steps.append({"step": 3, "title": "Detecting Skill Gaps", "status": "processing", "detail": f"Comparing skills against {career_goal} requirements..."})
    skill_gaps = detect_skill_gaps(profile, career_goal, model)
    reasoning_steps[-1]["status"] = "complete"
    reasoning_steps[-1]["detail"] = f"Match: {skill_gaps.get('match_percentage', 0)}% | Missing: {len(skill_gaps.get('missing_critical_skills', []))} critical skills"

    # Step 4: Roadmap Generation
    reasoning_steps.append({"step": 4, "title": "Creating Personalized Roadmap", "status": "processing", "detail": "Building 30/90/180-day learning plan..."})
    roadmap = generate_roadmap(profile, career_goal, skill_gaps, model)
    reasoning_steps[-1]["status"] = "complete"
    reasoning_steps[-1]["detail"] = "30-day, 90-day, and 6-month plans generated with projects and certifications."

    # Step 5: Reasoning Explanation
    reasoning_steps.append({"step": 5, "title": "Foundry IQ: Generating Grounded Reasoning", "status": "processing", "detail": "Synthesizing enterprise knowledge to explain recommendations..."})
    reasoning_chain = generate_reasoning_explanation(profile, career_goal, skill_gaps, model)
    reasoning_steps[-1]["status"] = "complete"
    reasoning_steps[-1]["detail"] = f"Generated {len(reasoning_chain)} Foundry IQ grounded reasoning steps."

    # Step 6: Confidence Score
    reasoning_steps.append({"step": 6, "title": "Calculating Career Match Score", "status": "processing", "detail": "Computing confidence score with weighted factors..."})
    confidence = calculate_confidence_score(profile, career_goal, skill_gaps, profile_analysis)
    reasoning_steps[-1]["status"] = "complete"
    reasoning_steps[-1]["detail"] = f"Career Match Score: {confidence.get('overall_score', 0)}% — {confidence.get('label', '')}"

    # Step 7: Final Response Assembly
    reasoning_steps.append({"step": 7, "title": "Assembling Recommendations", "status": "complete", "detail": "All analysis complete. Generating your personalized career report."})

    return {
        "reasoning_steps": reasoning_steps,
        "profile_analysis": profile_analysis,
        "skill_gaps": skill_gaps,
        "roadmap": roadmap,
        "reasoning_chain": reasoning_chain,
        "confidence_score": confidence,
        "career_goal": career_goal,
        "career_data": CAREER_SKILL_MAP.get(career_goal, {}),
    }


def generate_agent_chat_response(
    messages: List[Dict[str, str]],
    user_profile: Dict[str, Any],
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    RAG-powered intelligent chat response.
    - Retrieves relevant career knowledge chunks based on the latest user message.
    - Injects them into the system prompt as grounded context.
    - Agent acts as a mentor/dream-helper, not a form-filler.
    Returns structured response with thinking steps + final message.
    """
    from datetime import datetime
    _, model_id = _client(model)
    today = datetime.now().strftime("%A, %d %B %Y")

    # ── Foundry IQ: build query and ground context ───────────────────────────────
    user_query = ""
    for msg in reversed(messages):
        if msg.get("role") == "user":
            user_query = msg.get("content", "")
            break

    # Also blend in the career goal from profile if present
    career_goal = user_profile.get("career_goal", "") or user_profile.get("interests", "")
    rag_query = f"{user_query} {career_goal}".strip()
    
    from app.services.foundry_iq import foundry_iq
    iq_context = foundry_iq.retrieve_and_ground_context(rag_query, top_k=4, max_chars=3500) if rag_query else {"grounded_text": ""}
    rag_context = iq_context.get("grounded_text", "")

    # ── Build system prompt ───────────────────────────────────────────────────
    profile_summary = ""
    if user_profile:
        known = {k: v for k, v in user_profile.items() if v and v != "" and v != []}
        if known:
            profile_summary = f"\n\n### What I know about this user so far:\n{json.dumps(known, indent=2)}"

    rag_section = ""
    if rag_context:
        rag_section = f"\n\n### FOUNDRY IQ KNOWLEDGE GROUNDING (use this to ground your answer):\n{rag_context}"

    AGENT_SYSTEM_PROMPT = f"""You are CareerCoach AI — a warm, brilliant AI mentor dedicated to helping students achieve their dreams.

## TEMPORAL AWARENESS
Today's date is **{today}**.
Your training data has a knowledge cutoff. For real-time facts (current political leaders, election results, live news, stock prices, recent events after your cutoff) you MUST:
1. Clearly state your knowledge cutoff limitation.
2. Recommend the user verify via Google, Wikipedia, or a news source.
3. Never fabricate or guess current facts — always say "As of my last training data..." and flag the uncertainty.

## WHO YOU ARE
You are NOT a rigid form or a structured questionnaire. You are a trusted mentor — like a brilliant senior friend who happens to know everything about tech careers, learning paths, salaries, interviews, freelancing, and life as a student.

You have two modes:
1. **Career Expert**: When the conversation is about careers, skills, learning, jobs, interviews, projects, or studies — give deep, specific, personalized advice grounded in the knowledge base provided.
2. **Helpful Friend**: When someone asks a random question (movies, cricket, general knowledge, jokes, life advice, anything) — just answer it naturally and warmly, like a knowledgeable friend would. Don't refuse.

## YOUR PERSONALITY
- Warm, encouraging, and direct — never cold or robotic.
- You celebrate students' progress and potential.
- You use emojis sparingly but effectively for structure and warmth.
- You NEVER ask for name, degree, CGPA, or any personal info upfront.
- If context is helpful, you ask ONE natural question at a time only when it genuinely improves your advice.
- You NEVER say "I need your name/CGPA/degree to help you." That's gatekeeping help, and you don't do that.

## CAREER REASONING (when relevant)
When discussing careers:
1. **Reason step by step**: Don't just list things. Explain WHY you recommend what you do.
2. **Be specific**: Name exact courses, platforms, tools, companies — not vague generalities.
3. **Use the retrieved knowledge** (provided below) to give grounded, accurate answers.
4. **Adapt to what they share**: Use whatever context they give you — even a simple "I want to be an AI engineer" is enough to start.
5. **Detect career signals naturally**: If someone mentions their skills, background, or goals in passing — use that info without making a big deal of it.

## WHAT YOU NEVER DO
- Never say "Could you please share your name, degree, CGPA..." as an opener
- Never give a questionnaire or checklist of things to fill out
- Never block helping someone because they didn't provide info
- Never say "I'm just an AI" as a cop-out
- Never give one-line generic answers when depth is needed
- Never fabricate real-time facts — always flag knowledge cutoff uncertainty
{profile_summary}{rag_section}
"""

    try:
        response_text = chat_complete(
            messages=messages,
            system_prompt=AGENT_SYSTEM_PROMPT,
            model_hint=model_id,
            temperature=0.5,
            max_tokens=1500,
        )

        # Detect if the agent has enough info to trigger full analysis
        should_analyze = any(word in response_text.lower() for word in [
            "roadmap", "skill gap", "personalized plan", "based on your background",
            "career match", "missing skills", "you should learn", "here's your plan",
            "let me analyze", "gap analysis"
        ])

        return {
            "message": response_text,
            "should_trigger_analysis": should_analyze,
            "reasoning_hint": "Processing your query..." if not should_analyze else "Foundry IQ is analyzing career trajectory...",
            "rag_sources": len(rag_context) > 0,
        }
    except Exception as e:
        return {
            "message": f"I hit a snag: {str(e)[:100]}. Try again in a moment!",
            "should_trigger_analysis": False,
            "reasoning_hint": "Error occurred",
            "rag_sources": False,
        }
