"""
groq_services.py — CareerCoach AI
Handles structured JSON generation tasks: interview questions, answer evaluation,
resume/JD comparison, and career opportunity suggestions.

All AI calls now go through the unified ai_provider.chat_complete() which
auto-selects Gemini or Groq and falls back between them.
"""
import json
import re
from typing import Any, Dict, List, Optional

from app.core.ai_provider import chat_complete


def _extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()
    # Strip markdown fences if present
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"\s*```$", "", text)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    raise ValueError("Model did not return valid JSON")


def default_evaluation(answer: str) -> Dict[str, Any]:
    return {
        "is_relevant": False,
        "relevance_score": 0,
        "evaluation_mode": "off_topic",
        "overall_score": 0,
        "dimension_scores": {
            "technical_accuracy": 0,
            "problem_solving": 0,
            "communication": 0,
            "structure": 0,
            "completeness": 0,
            "confidence": 0,
        },
        "strengths": [],
        "improvements": ["Provide a meaningful answer relevant to the question."],
        "missed_points": ["No meaningful answer was submitted."],
        "feedback_summary": "The answer was empty or could not be parsed.",
        "hiring_signal": "weak",
        "difficulty_recommendation": "easier",
        "follow_up_question": "Can you try answering the question again in your own words?",
    }


def generate_interview_question(
    role: str,
    interview_type: str,
    difficulty: str,
    field_of_study: Optional[str] = None,
    model: Optional[str] = None,
    previous_questions: Optional[List[str]] = None,
    coaching_style: Optional[str] = None,
) -> Dict[str, Any]:
    prev = ""
    if previous_questions:
        prev = f"\nDO NOT repeat or overlap with these previous questions: {json.dumps(previous_questions)}"

    style_map = {
        "strict":      "Be a rigorous, demanding interviewer. Ask tough follow-ups.",
        "supportive":  "Be encouraging and supportive. Frame questions positively.",
        "academic":    "Use structured, criteria-based academic framing.",
        "speed_drill": "Keep questions short and punchy for rapid-fire practice.",
    }
    style_hint = style_map.get(coaching_style or "supportive", "")

    field_context = ""
    if field_of_study:
        field_context = f"The candidate's field of study is {field_of_study}. "
        if "arts" in field_of_study.lower() or "literature" in field_of_study.lower():
            field_context += "Focus on how their skills (communication, critical thinking, creativity) transfer to the corporate role."

    empty_shape = json.dumps({
        "question_text": "",
        "expected_answer_points": [],
        "category": "",
        "difficulty": difficulty,
    })

    prompt = f"""Generate exactly one interview question.{prev}
Rules:
- Match role: {role}, type: {interview_type}, difficulty: {difficulty}
- {field_context}
- expected_answer_points: 4-6 short bullet-style points
- category: backend, databases, api, system_design, hr, behavioral, debugging, ops
Use this JSON shape (fill all fields):
{empty_shape}
"""

    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt=(
                "You are an expert interviewer. " + style_hint +
                " Return ONLY valid JSON, no markdown. Do not add any text outside JSON."
            ),
            model_hint=model,
            temperature=0.7,
            max_tokens=800,
        )
        parsed = _extract_json_object(raw)
    except Exception as e:
        return {
            "question_text": f"Describe a recent project where you played a key role. (Fallback: {str(e)[:50]})",
            "expected_answer_points": ["Situation", "Task", "Action", "Result"],
            "category": "behavioral",
            "difficulty": difficulty,
        }

    parsed.setdefault("question_text", "")
    parsed.setdefault("expected_answer_points", [])
    parsed.setdefault("category", interview_type)
    parsed.setdefault("difficulty", difficulty)
    if not parsed.get("question_text"):
        raise ValueError("Generated question is empty")
    if not isinstance(parsed.get("expected_answer_points"), list):
        parsed["expected_answer_points"] = []
    return parsed


def evaluate_interview_answer(
    role: str,
    question: str,
    answer: str,
    expected_points: Optional[List[str]] = None,
    difficulty: str = "medium",
    interview_type: str = "technical",
    model: Optional[str] = None,
    coaching_style: Optional[str] = None,
) -> Dict[str, Any]:
    if not (answer or "").strip():
        return default_evaluation(answer or "")

    style_map = {
        "strict":      "Be harsh but fair. Highlight every gap.",
        "supportive":  "Be encouraging. Focus on strengths while noting improvements.",
        "academic":    "Evaluate using structured academic criteria.",
        "speed_drill": "Keep feedback very brief and direct.",
    }
    style_hint = style_map.get(coaching_style or "supportive", "")
    expected_points = expected_points or []

    system = (
        "You evaluate interview answers. " + style_hint +
        " Reply with ONLY valid JSON matching the schema. Scores are integers 0-100."
    )
    if interview_type == "communication":
        system += (
            " This is a Communication Practice session. Evaluate delivery, pronunciation, "
            "pace, fluency, filler words, structure, confidence, and clarity. "
            "Technical correctness is secondary."
        )

    user = f"""Role: {role}
Interview type: {interview_type}
Difficulty: {difficulty}
Question: {question}
Expected concept points: {json.dumps(expected_points)}
Candidate answer: {answer}

Return JSON with keys:
overall_score, feedback_summary, strengths (array), improvements (array), missed_points (array),
hiring_signal (weak|moderate|strong), difficulty_recommendation (easier|same|harder),
problem_solving_score, technical_score, communication_score, structure_score,
completeness_score, confidence_score, follow_up_question (string or null)
"""

    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": user}],
            system_prompt=system,
            model_hint=model,
            temperature=0.2,
            max_tokens=1000,
        )
        parsed = _extract_json_object(raw)
    except Exception:
        return default_evaluation(answer)

    parsed.setdefault("overall_score", 0)
    parsed.setdefault("feedback_summary", "")
    parsed.setdefault("strengths", [])
    parsed.setdefault("improvements", [])
    parsed.setdefault("missed_points", [])
    parsed.setdefault("hiring_signal", "weak")
    parsed.setdefault("difficulty_recommendation", "same")
    for k in (
        "problem_solving_score", "technical_score", "communication_score",
        "structure_score", "completeness_score", "confidence_score",
    ):
        parsed.setdefault(k, 0)
    return parsed


def analyze_resume_vs_jd(resume_content: str, jd_text: str, model: Optional[str] = None) -> Dict[str, Any]:
    user = f"""Compare this resume to the job description.

Resume:
{resume_content[:12000]}

Job description:
{jd_text[:12000]}

Return JSON with:
match_percentage (0-100),
missing_keywords (array of strings),
suggestions (array of strings),
summary (string)
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": user}],
            system_prompt="You are an expert ATS and recruiter assistant. Reply with ONLY valid JSON.",
            model_hint=model,
            temperature=0.2,
            max_tokens=1000,
        )
        parsed = _extract_json_object(raw)
        parsed.setdefault("match_percentage", 0)
        parsed.setdefault("missing_keywords", [])
        parsed.setdefault("suggestions", [])
        parsed.setdefault("summary", "")
        return parsed
    except Exception:
        return {"match_percentage": 0, "missing_keywords": [], "suggestions": [], "summary": "Analysis unavailable."}


def suggest_career_opportunities(
    field_of_study: str,
    education_level: Optional[str] = None,
    model: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Suggest MNC roles and career pathways based on field of study."""
    prompt = f"""Suggest 5 innovative corporate/MNC job roles for a candidate with a background in: {field_of_study} ({education_level or 'Undergraduate'}).

For each role, provide:
- role_title (string)
- description (string, why it fits their major)
- key_skills_to_highlight (list of strings)
- typical_salary_range (string)
- mnc_companies (list of examples)

Return ONLY a valid JSON array of objects in this exact format:
[
  {{
    "role_title": "UX Writer",
    "description": "Your literature background helps in creating clear, empathetic microcopy.",
    "key_skills_to_highlight": ["Storytelling", "Editing", "User Research"],
    "typical_salary_range": "$60k - $120k",
    "mnc_companies": ["Google", "Spotify", "Microsoft"]
  }}
]
"""
    try:
        raw = chat_complete(
            messages=[{"role": "user", "content": prompt}],
            system_prompt="You are an expert career consultant. Return ONLY valid JSON as a list of objects.",
            model_hint=model,
            temperature=0.7,
            max_tokens=1500,
        )
        # Try to parse as list first, then as dict with "opportunities" key
        text = raw.strip()
        text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
        text = re.sub(r"\s*```$", "", text)
        parsed = json.loads(text)
        if isinstance(parsed, dict) and "opportunities" in parsed:
            return parsed["opportunities"]
        if isinstance(parsed, list):
            return parsed
        return []
    except Exception:
        return []
