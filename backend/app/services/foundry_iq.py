"""
Microsoft Foundry IQ Layer Integration
======================================
This module simulates the Microsoft Foundry IQ architectural pattern, providing
a dedicated knowledge and reasoning intelligence layer for the AI agent.

It connects structured profile data with unstructured knowledge base data, ensuring
all agent reasoning is "grounded" in enterprise-level context before generating
insights or roadmaps.
"""
import json
from typing import Any, Dict, List, Optional
from datetime import datetime

from app.core.ai_provider import chat_complete
from app.services.rag_knowledge import retrieve_context, retrieve_context_text

class FoundryIQLayer:
    """
    Foundry IQ Intelligence Layer.
    Provides semantic data grounding, multi-step reasoning, and Work IQ fusion.
    """
    
    def __init__(self):
        self.layer_name = "Microsoft_Foundry_IQ_Simulated"

    def retrieve_and_ground_context(self, query: str, top_k: int = 4, max_chars: int = 3500) -> Dict[str, Any]:
        """
        Retrieves knowledge base chunks and returns both raw structured data and formatted text
        for grounding the agent's context.
        
        Now uses the enhanced rag_service for better retrieval.
        """
        from app.services import rag_service
        
        chunks = rag_service.retrieve_context(query, top_k=top_k)
        text_context = rag_service.retrieve_context_text(query, top_k=top_k, max_chars=max_chars)
        
        return {
            "is_grounded": len(chunks) > 0,
            "raw_chunks": chunks,
            "grounded_text": text_context
        }

    def generate_grounded_reasoning(
        self, 
        profile: Dict[str, Any], 
        career_goal: str, 
        skill_gaps: Dict[str, Any], 
        model_id: Optional[str] = None
    ) -> List[Dict[str, str]]:
        """
        Synthesizes reasoning by explicitly forcing the AI to evaluate the grounded context
        against the user profile. This represents the reasoning/Foundry IQ step.
        """
        # Grounding context retrieval
        iq_context = self.retrieve_and_ground_context(f"{career_goal} skills learning path", top_k=3)
        
        missing = skill_gaps.get("missing_critical_skills", [])
        present = skill_gaps.get("current_skills_present", [])
        priority_order = skill_gaps.get("priority_learning_order", [])

        prompt = f"""
[FOUNDRY IQ KNOWLEDGE GROUNDING INITIATED]
You are operating within the Foundry IQ reasoning layer. Your task is to explain the reasoning behind career recommendations using a clear chain-of-thought format. You MUST ground your reasoning in the provided enterprise knowledge context.

## ENTERPRISE KNOWLEDGE CONTEXT
{iq_context['grounded_text']}

## USER PROFILE DATA (Work IQ Fusion)
Student wants to be: {career_goal}
Their skills: {profile.get("skills", [])}
Relevant skills present: {present}
Critical missing skills: {missing}
Learning priority: {priority_order}

## REASONING TASK
Analyze the User Profile against the Enterprise Knowledge Context. 
Return ONLY a valid JSON array of reasoning steps demonstrating your logic:
[
  {{"step": 1, "thought": "Clear reasoning statement referencing knowledge context", "conclusion": "Action or insight derived"}},
  {{"step": 2, "thought": "Next reasoning statement", "conclusion": "Action or insight"}},
  ...
]
Provide 5-7 logical reasoning steps that flow naturally and explicitly mention industry standards or knowledge from the context.
"""
        try:
            raw = chat_complete(
                messages=[{"role": "user", "content": prompt}],
                system_prompt="You are the Foundry IQ reasoning engine. Generate transparent, grounded reasoning chains. Return ONLY a valid JSON array.",
                model_hint=model_id,
                temperature=0.3,
                max_tokens=2000,
            )
            # Strip markdown fences safely
            text = raw.strip()
            import re
            text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
            text = re.sub(r"\s*```$", "", text)
            try:
                result = json.loads(text)
            except json.JSONDecodeError:
                m = re.search(r"\[[\s\S]*\]", text)
                result = json.loads(m.group(0)) if m else []
                
            if isinstance(result, list):
                return result
            return []
        except Exception as e:
            return [
                {"step": 1, "thought": f"Analyzed user goal for {career_goal} using Foundry IQ layer.", "conclusion": "Initiating grounding..."},
                {"step": 2, "thought": f"Found missing skills: {', '.join(missing[:3])}.", "conclusion": "Prioritized learning based on industry gaps."},
                {"step": 3, "thought": f"System error during full deep reasoning: {str(e)[:50]}", "conclusion": "Fallen back to basic heuristic reasoning."}
            ]

# Singleton instance
foundry_iq = FoundryIQLayer()
