"""
Generates structured, evidence-cited answers using an LLM.
"""
import json
from typing import Optional
from ..config import get_settings
from ..schemas.ask import AskResponse, EvidenceItem, TimelineItem, KnownInferred
import uuid
from datetime import datetime

settings = get_settings()

ANSWER_SYSTEM_PROMPT = """You are Codebase Archaeologist, an expert at explaining why code exists by analyzing commit history, pull requests, issues, and discussions.

You will be given:
1. A question about a codebase
2. Retrieved evidence (commits, PRs, issues, comments, code snippets)

Your task is to produce a structured JSON answer. STRICT RULES:
- Only cite facts supported by the provided evidence
- Use citation labels like [1], [2], [3] inline in your answer
- If evidence is weak or missing, say so honestly
- Do NOT invent reasons, authors, or events not in evidence
- Be concise but complete

Return ONLY valid JSON with this exact structure:
{
  "answer": "Direct 3-6 sentence answer with [1], [2] citations",
  "confidence": 0.85,
  "confidence_explanation": "One sentence explaining why confidence is this level",
  "known": ["fact directly supported by evidence", ...],
  "inferred": ["reasonable conclusion from evidence", ...],
  "unknown": ["information missing from evidence", ...],
  "timeline": [
    {
      "date": "2024-01-15T00:00:00",
      "event_type": "commit|pr_created|pr_merged|issue_opened|issue_closed|comment",
      "title": "Short title",
      "description": "Why this matters",
      "citation_id": "[1]"
    }
  ],
  "related_files": ["path/to/related/file.py", ...],
  "follow_up_questions": [
    "Show me the PR that introduced this",
    "Find later bugs related to this file",
    "Who should I ask about this module?"
  ]
}"""


def _build_evidence_context(evidence: list[EvidenceItem]) -> str:
    parts = []
    for item in evidence:
        date_str = item.date.strftime("%Y-%m-%d") if item.date else "unknown date"
        parts.append(
            f"{item.citation_label} [{item.source_type.upper()}] {item.title}\n"
            f"  Author: {item.author or 'unknown'} | Date: {date_str}\n"
            f"  {item.snippet[:400]}\n"
        )
    return "\n".join(parts)


async def generate_answer(
    question: str,
    evidence: list[EvidenceItem],
    repo_name: str,
    context_file: Optional[str] = None,
) -> AskResponse:
    evidence_context = _build_evidence_context(evidence)

    user_prompt = f"""Repository: {repo_name}
{"File context: " + context_file if context_file else ""}

Question: {question}

Retrieved Evidence:
{evidence_context}

Now produce the structured JSON answer."""

    raw_json = await _call_llm(user_prompt)
    return _parse_response(raw_json, evidence)


async def _call_llm(user_prompt: str) -> str:
    provider = settings.llm_provider.lower()

    if provider == "anthropic" and settings.anthropic_api_key:
        return await _call_anthropic(user_prompt)
    elif provider == "openai" and settings.openai_api_key:
        return await _call_openai(user_prompt)
    else:
        return _fallback_answer(user_prompt)


async def _call_anthropic(user_prompt: str) -> str:
    try:
        import anthropic
        client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
        msg = await client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2000,
            system=ANSWER_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return msg.content[0].text
    except Exception as e:
        return _fallback_answer(f"LLM error: {e}")


async def _call_openai(user_prompt: str) -> str:
    try:
        import openai
        client = openai.AsyncOpenAI(api_key=settings.openai_api_key)
        resp = await client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": ANSWER_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            max_tokens=2000,
            response_format={"type": "json_object"},
        )
        return resp.choices[0].message.content
    except Exception as e:
        return _fallback_answer(f"LLM error: {e}")


def _fallback_answer(context: str) -> str:
    """Returns a minimal valid JSON when no LLM is configured."""
    return json.dumps({
        "answer": "No LLM provider is configured. Configure ANTHROPIC_API_KEY or OPENAI_API_KEY to get AI-generated answers. The evidence below was retrieved based on your question.",
        "confidence": 0.0,
        "confidence_explanation": "No LLM provider configured — answer is based on retrieved evidence only.",
        "known": [],
        "inferred": [],
        "unknown": ["LLM answer generation requires API key configuration"],
        "timeline": [],
        "related_files": [],
        "follow_up_questions": [
            "Configure an LLM provider in Settings to get AI answers",
        ],
    })


def _parse_response(raw: str, evidence: list[EvidenceItem]) -> AskResponse:
    """Parses LLM JSON response into structured AskResponse."""
    try:
        # Strip markdown code blocks if present
        raw = raw.strip()
        if raw.startswith("```"):
            raw = raw[raw.find("\n") + 1:]
        if raw.endswith("```"):
            raw = raw[:raw.rfind("```")]

        data = json.loads(raw.strip())
    except Exception:
        data = {
            "answer": raw[:1000] if raw else "Unable to parse response.",
            "confidence": 0.3,
            "confidence_explanation": "Response parsing failed.",
            "known": [],
            "inferred": [],
            "unknown": [],
            "timeline": [],
            "related_files": [],
            "follow_up_questions": [],
        }

    timeline = []
    for t in data.get("timeline", []):
        try:
            date = datetime.fromisoformat(t.get("date", "").replace("Z", "")) if t.get("date") else None
        except Exception:
            date = None
        timeline.append(TimelineItem(
            date=date,
            event_type=t.get("event_type", "commit"),
            title=t.get("title", ""),
            description=t.get("description"),
            author=t.get("author"),
            citation_id=t.get("citation_id"),
        ))

    return AskResponse(
        question_id=str(uuid.uuid4()),
        answer=data.get("answer", ""),
        confidence=float(data.get("confidence", 0.5)),
        confidence_explanation=data.get("confidence_explanation", ""),
        timeline=timeline,
        evidence=evidence,
        known_vs_inferred=KnownInferred(
            known=data.get("known", []),
            inferred=data.get("inferred", []),
            unknown=data.get("unknown", []),
        ),
        related_files=data.get("related_files", []),
        follow_up_questions=data.get("follow_up_questions", []),
    )
