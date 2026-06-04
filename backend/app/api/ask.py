from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database import get_session
from ..models import Repository, Question, AnswerEvidence
from ..schemas.ask import AskRequest, AskResponse
from ..services.retrieval import retrieve_evidence
from ..services.answer_generation import generate_answer

router = APIRouter(prefix="/api/repositories/{repo_id}", tags=["ask"])


@router.post("/ask", response_model=AskResponse)
async def ask_question(
    repo_id: str,
    body: AskRequest,
    session: AsyncSession = Depends(get_session),
):
    repo = (await session.execute(
        select(Repository).where(Repository.id == repo_id)
    )).scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Repository is not ready for queries (status: {repo.status})"
        )

    # Retrieve evidence
    evidence = await retrieve_evidence(
        session=session,
        repo_id=repo_id,
        question=body.question,
        context_file_path=body.context.file_path if body.context else None,
        context_symbol=body.context.symbol_name if body.context else None,
    )

    # Generate answer
    response = await generate_answer(
        question=body.question,
        evidence=evidence,
        repo_name=f"{repo.owner}/{repo.name}",
        context_file=body.context.file_path if body.context else None,
    )

    # Persist question + evidence
    question_record = Question(
        repository_id=repo_id,
        question_text=body.question,
        answer_text=response.answer,
        confidence=response.confidence,
        context=body.context.model_dump() if body.context else None,
        timeline=[t.model_dump() for t in response.timeline],
        related_files=response.related_files,
        follow_up_questions=response.follow_up_questions,
    )
    session.add(question_record)
    await session.flush()

    for ev in evidence:
        record = AnswerEvidence(
            question_id=question_record.id,
            source_type=ev.source_type,
            source_id=ev.source_id or ev.id,
            snippet=ev.snippet,
            relevance_score=ev.relevance_score,
            citation_label=ev.citation_label,
            title=ev.title,
            author=ev.author,
            date=ev.date,
            github_url=ev.github_url,
        )
        session.add(record)

    await session.commit()
    response.question_id = question_record.id
    return response


@router.get("/questions")
async def list_questions(repo_id: str, session: AsyncSession = Depends(get_session)):
    """Returns question history for this repository."""
    questions = (await session.execute(
        select(Question)
        .where(Question.repository_id == repo_id)
        .order_by(Question.created_at.desc())
        .limit(50)
    )).scalars().all()
    return [
        {
            "id": q.id,
            "question": q.question_text,
            "answer_preview": (q.answer_text or "")[:200],
            "confidence": q.confidence,
            "created_at": q.created_at.isoformat(),
        }
        for q in questions
    ]
