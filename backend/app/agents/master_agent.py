"""Master agent: orchestrates the full pipeline.

3 Claude API calls:
1. Parse case text → FactPattern
2. After Wave 1 — synthesize statutes
3. After Wave 2 — synthesize case law

Sub-agents run in parallel via asyncio.gather.
"""

import asyncio
import json
import logging

from app.core.run_store import RunState
from app.core.sse_manager import sse_manager
from app.models.events import StreamEvent, EventType
from app.models.schemas import (
    FactPattern,
    LegalIssue,
    StatuteResult,
    CaseLawResult,
)
from app.services.claude_client import ClaudeClient
from app.services.courtlistener import CourtListenerClient
from app.agents.prompts import (
    FACT_PATTERN_SYSTEM,
    FACT_PATTERN_USER,
    MASTER_SYNTHESIZE_STATUTES_SYSTEM,
    MASTER_SYNTHESIZE_STATUTES_USER,
    MASTER_SYNTHESIZE_CASES_SYSTEM,
    MASTER_SYNTHESIZE_CASES_USER,
)
from app.agents.statute_agent import run_statute_agent
from app.agents.caselaw_agent import run_caselaw_agent

logger = logging.getLogger(__name__)


async def run_master_pipeline(run: RunState) -> None:
    """Full pipeline orchestrator.

    Submit case → Master parses → FactPattern (emit SSE)
        → Wave 1: parallel statute agents (emit progress + results)
        → Master synthesizes statutes (emit wave1_complete)
        → Wave 2: parallel case law agents (emit progress + results)
        → Master synthesizes case law (emit wave2_complete)
        → Emit run_complete
    """
    claude = ClaudeClient()
    cl_client = CourtListenerClient()

    try:
        await _execute_pipeline(run, claude, cl_client)
    finally:
        await cl_client.close()


async def _execute_pipeline(
    run: RunState,
    claude: ClaudeClient,
    cl_client: CourtListenerClient,
) -> None:
    # === Emit run_started ===
    await sse_manager.emit(
        run.run_id,
        StreamEvent(type=EventType.RUN_STARTED, payload={"run_id": run.run_id}),
    )

    # === Call 1: Parse case text → FactPattern ===
    user_prompt = FACT_PATTERN_USER.format(case_text=run.input_text)
    fp_data = await claude.generate_json(FACT_PATTERN_SYSTEM, user_prompt)

    fact_pattern = FactPattern(
        summary=fp_data.get("summary", ""),
        parties=fp_data.get("parties", []),
        issues=[
            LegalIssue(**issue_data)
            for issue_data in fp_data.get("issues", [])[:4]
        ],
        jurisdiction=fp_data.get("jurisdiction", "California"),
    )
    run.fact_pattern = fact_pattern

    await sse_manager.emit(
        run.run_id,
        StreamEvent(type=EventType.FACT_PATTERN, payload=fact_pattern.model_dump()),
    )

    # === Wave 1: Parallel statute agents ===
    await sse_manager.emit(
        run.run_id,
        StreamEvent(
            type=EventType.WAVE1_STARTED,
            payload={"issue_count": len(fact_pattern.issues)},
        ),
    )

    # Run one sub-agent per issue slice, in parallel
    statute_tasks = []
    for issue in fact_pattern.issues:
        statute_tasks.append(
            _run_statute_with_progress(run.run_id, issue, fact_pattern, claude)
        )

    statute_results_nested = await asyncio.gather(*statute_tasks, return_exceptions=True)

    # Flatten results, skip exceptions
    all_statute_candidates: list[StatuteResult] = []
    for result in statute_results_nested:
        if isinstance(result, Exception):
            logger.error(f"Statute agent failed: {result}")
            continue
        all_statute_candidates.extend(result)

    # === Call 2: Master synthesizes statutes ===
    if all_statute_candidates:
        candidates_json = json.dumps(
            [s.model_dump() for s in all_statute_candidates], indent=2
        )
        synth_prompt = MASTER_SYNTHESIZE_STATUTES_USER.format(
            fact_summary=fact_pattern.summary,
            candidates_json=candidates_json,
        )
        synth_data = await claude.generate_json(
            MASTER_SYNTHESIZE_STATUTES_SYSTEM, synth_prompt
        )

        final_statutes: list[StatuteResult] = []
        for s in synth_data.get("ranked_statutes", [])[:4]:
            # Find the original full_text and url from candidates
            original = next(
                (c for c in all_statute_candidates if c.code == s.get("code") and c.section == s.get("section")),
                None,
            )
            final_statutes.append(
                StatuteResult(
                    code=s.get("code", ""),
                    section=s.get("section", ""),
                    title=s.get("title", ""),
                    full_text=original.full_text if original else "",
                    url=original.url if original else "",
                    relevance_summary=s.get("relevance_summary", ""),
                    case_snippet=s.get("case_snippet", ""),
                    confidence=s.get("confidence", 0.5),
                    source_issue_id=s.get("source_issue_id", ""),
                )
            )
        run.statutes = final_statutes
    else:
        run.statutes = []

    await sse_manager.emit(
        run.run_id,
        StreamEvent(
            type=EventType.WAVE1_COMPLETE,
            payload={"statutes": [s.model_dump() for s in run.statutes]},
        ),
    )

    # === Wave 2: Parallel case law agents ===
    await sse_manager.emit(
        run.run_id,
        StreamEvent(
            type=EventType.WAVE2_STARTED,
            payload={"statute_count": len(run.statutes)},
        ),
    )

    # Build a mapping from source_issue_id to issue for lookup
    issue_map = {issue.id: issue for issue in fact_pattern.issues}

    caselaw_tasks = []
    for statute in run.statutes:
        issue = issue_map.get(statute.source_issue_id, fact_pattern.issues[0] if fact_pattern.issues else None)
        if issue:
            caselaw_tasks.append(
                _run_caselaw_with_progress(
                    run.run_id, statute, issue, fact_pattern, claude, cl_client
                )
            )

    caselaw_results_nested = await asyncio.gather(*caselaw_tasks, return_exceptions=True)

    all_caselaw_candidates: list[CaseLawResult] = []
    for result in caselaw_results_nested:
        if isinstance(result, Exception):
            logger.error(f"Case law agent failed: {result}")
            continue
        all_caselaw_candidates.extend(result)

    # === Call 3: Master synthesizes case law ===
    if all_caselaw_candidates:
        candidates_json = json.dumps(
            [c.model_dump() for c in all_caselaw_candidates], indent=2
        )
        statutes_summary = "\n".join(
            f"- {s.code} {s.section}: {s.title}" for s in run.statutes
        )
        synth_prompt = MASTER_SYNTHESIZE_CASES_USER.format(
            fact_summary=fact_pattern.summary,
            statutes_summary=statutes_summary,
            candidates_json=candidates_json,
        )
        synth_data = await claude.generate_json(
            MASTER_SYNTHESIZE_CASES_SYSTEM, synth_prompt
        )

        final_cases: list[CaseLawResult] = []
        for c in synth_data.get("ranked_cases", [])[:4]:
            final_cases.append(
                CaseLawResult(
                    case_name=c.get("case_name", ""),
                    citation=c.get("citation", ""),
                    court=c.get("court", ""),
                    date_filed=c.get("date_filed", ""),
                    url=c.get("url", ""),
                    snippet=c.get("snippet", ""),
                    relevance_summary=c.get("relevance_summary", ""),
                    related_statutes=c.get("related_statutes", []),
                    confidence=c.get("confidence", 0.5),
                    source_issue_id=c.get("source_issue_id", ""),
                )
            )
        run.case_law = final_cases
    else:
        run.case_law = []

    await sse_manager.emit(
        run.run_id,
        StreamEvent(
            type=EventType.WAVE2_COMPLETE,
            payload={"case_law": [c.model_dump() for c in run.case_law]},
        ),
    )

    # === Emit run_complete ===
    await sse_manager.emit(
        run.run_id,
        StreamEvent(
            type=EventType.RUN_COMPLETE,
            payload=run.to_final_result().model_dump(),
        ),
    )


async def _run_statute_with_progress(
    run_id: str,
    issue: LegalIssue,
    fact_pattern: FactPattern,
    claude: ClaudeClient,
) -> list[StatuteResult]:
    """Run statute agent with SSE progress events."""
    await sse_manager.emit(
        run_id,
        StreamEvent(
            type=EventType.STATUTE_PROGRESS,
            payload={"issue_id": issue.id, "status": "searching", "label": issue.label},
        ),
    )

    results = await run_statute_agent(issue, fact_pattern, claude)

    for statute in results:
        await sse_manager.emit(
            run_id,
            StreamEvent(
                type=EventType.STATUTE_FOUND,
                payload=statute.model_dump(),
            ),
        )

    await sse_manager.emit(
        run_id,
        StreamEvent(
            type=EventType.STATUTE_PROGRESS,
            payload={
                "issue_id": issue.id,
                "status": "complete",
                "label": issue.label,
                "count": len(results),
            },
        ),
    )

    return results


async def _run_caselaw_with_progress(
    run_id: str,
    statute: StatuteResult,
    issue: LegalIssue,
    fact_pattern: FactPattern,
    claude: ClaudeClient,
    cl_client: CourtListenerClient,
) -> list[CaseLawResult]:
    """Run case law agent with SSE progress events."""
    await sse_manager.emit(
        run_id,
        StreamEvent(
            type=EventType.CASELAW_PROGRESS,
            payload={
                "statute": f"{statute.code} {statute.section}",
                "status": "searching",
            },
        ),
    )

    results = await run_caselaw_agent(statute, issue, fact_pattern, claude, cl_client)

    for case in results:
        await sse_manager.emit(
            run_id,
            StreamEvent(
                type=EventType.CASELAW_FOUND,
                payload=case.model_dump(),
            ),
        )

    await sse_manager.emit(
        run_id,
        StreamEvent(
            type=EventType.CASELAW_PROGRESS,
            payload={
                "statute": f"{statute.code} {statute.section}",
                "status": "complete",
                "count": len(results),
            },
        ),
    )

    return results
