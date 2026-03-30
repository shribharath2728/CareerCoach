import json
import os
import re
from typing import Any, Dict, List, Optional

from groq import Groq

from app.core.groq_models import resolve_groq_model

def _client() -> Groq:
    key = os.getenv("GROQ_API_KEY")
    if not key:
        raise RuntimeError("GROQ_API_KEY is not set")
    base = os.getenv("GROQ_BASE_URL", "https://api.groq.com")
    return Groq(api_key=key, base_url=base)

def _extract_json_object(text: str) -> Dict[str, Any]:
    text = text.strip()
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
    model: Optional[str] = None,
    previous_questions: Optional[List[str]] = None,
) -> Dict[str, Any]:
    model_id = resolve_groq_model(model)
    prev = ""
    if previous_questions:
        prev = f"\nDO NOT repeat or overlap with these previous questions: {json.dumps(previous_questions)}"

    system = (
        "You are an expert interviewer. Return ONLY valid JSON, no markdown. "
        "Do not add any text outside JSON."
    )
    user = json.dumps(
        {
            "question_text": "",
            "expected_answer_points": [],
            "category": "",
            "difficulty": difficulty,
        }
    )
    prompt = f"""Generate exactly one interview question.{prev}
Rules:
- Match role: {role}, type: {interview_type}, difficulty: {difficulty}
- expected_answer_points: 4-6 short bullet-style points
- category should be like: backend, databases, api, system_design, hr, behavioral, debugging, ops
Use this JSON shape (fill all fields):
{user}
"""
    try:
        res = _client().chat.completions.create(
            model=model_id,
            temperature=0.7,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
        )
        content = res.choices[0].message.content or ""
        parsed = _extract_json_object(content)
    except Exception as e:
        # Fallback question if API fails
        return {
            "question_text": f"Could you describe a recent project where you played a key role? (Fallback due to: {str(e)[:50]}...)",
            "expected_answer_points": ["Context/Situation", "Action taken", "Personal contribution", "Outcome"],
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
) -> Dict[str, Any]:
    if not (answer or "").strip():
        return default_evaluation(answer or "")
    model_id = resolve_groq_model(model)
    expected_points = expected_points or []
    system = (
        "You evaluate interview answers. Reply with ONLY valid JSON matching the schema. "
        "Scores are integers 0-100."
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
        res = _client().chat.completions.create(
            model=model_id,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        content = res.choices[0].message.content or ""
        parsed = _extract_json_object(content)
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
        "problem_solving_score",
        "technical_score",
        "communication_score",
        "structure_score",
        "completeness_score",
        "confidence_score",
    ):
        parsed.setdefault(k, 0)
    return parsed

def analyze_resume_vs_jd(resume_content: str, jd_text: str, model: Optional[str] = None) -> Dict[str, Any]:
    model_id = resolve_groq_model(model)
    system = "You are an expert ATS and recruiter assistant. Reply with ONLY valid JSON."
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
    res = _client().chat.completions.create(
        model=model_id,
        temperature=0.2,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    content = res.choices[0].message.content or ""
    parsed = _extract_json_object(content)
    parsed.setdefault("match_percentage", 0)
    parsed.setdefault("missing_keywords", [])
    parsed.setdefault("suggestions", [])
    parsed.setdefault("summary", "")
    return parsed
