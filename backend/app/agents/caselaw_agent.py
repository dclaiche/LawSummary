"""Wave 2: Case law sub-agent.

Each agent gets one statute (from Wave 1) + full fact pattern.
Two-step tool-use pattern:
1. LLM generates search queries
2. Python executes searches against CourtListener
3. LLM evaluates results
"""

import logging

MAX_REQUESTS_PER_AGENT = 10

from app.models.schemas import LegalIssue, FactPattern, StatuteResult, CaseLawResult
from app.services.claude_client import ClaudeClient
from app.services.courtlistener import CourtListenerClient, CourtListenerSearchHit
from app.agents.prompts import (
    CASELAW_AGENT_SYSTEM,
    CASELAW_AGENT_USER,
    CASELAW_EVALUATE_SYSTEM,
    CASELAW_EVALUATE_USER,
)

logger = logging.getLogger(__name__)

CL_BASE = "https://www.courtlistener.com"


async def run_caselaw_agent(
    statute: StatuteResult,
    issue: LegalIssue,
    fact_pattern: FactPattern,
    claude: ClaudeClient,
    cl_client: CourtListenerClient,
) -> list[CaseLawResult]:
    """Run a case law research agent for a single statute.

    Args:
        statute: The statute to find case law for
        issue: The legal issue this statute addresses
        fact_pattern: The full fact pattern for context
        claude: Claude API client
        cl_client: CourtListener API client

    Returns:
        List of up to 2 CaseLawResult candidates.
    """
    # Step 1: Ask Claude to generate search queries
    user_prompt = CASELAW_AGENT_USER.format(
        code=statute.code,
        section=statute.section,
        title=statute.title,
        statute_text=statute.full_text[:2000],
        issue_label=issue.label,
        issue_description=issue.description,
        relevant_facts="\n".join(f"- {f}" for f in issue.relevant_facts),
        fact_summary=fact_pattern.summary,
    )

    try:
        search_plan = await claude.generate_json(CASELAW_AGENT_SYSTEM, user_prompt)
    except Exception as e:
        logger.error(f"Case law agent query generation failed for {statute.code} {statute.section}: {e}")
        return []

    # Step 2: Execute searches (capped at MAX_REQUESTS_PER_AGENT external requests)
    all_hits: dict[str, CourtListenerSearchHit] = {}
    request_count = 0

    for query in search_plan.get("search_queries", [])[:5]:
        if request_count >= MAX_REQUESTS_PER_AGENT:
            break
        try:
            request_count += 1
            hits = await cl_client.search(query, max_results=5)
            for hit in hits:
                key = f"{hit.case_name}:{hit.date_filed}"
                if key not in all_hits:
                    all_hits[key] = hit
        except Exception as e:
            logger.warning(f"CourtListener search failed for '{query}': {e}")

    if not all_hits:
        logger.info(f"No cases found for {statute.code} {statute.section}")
        return []

    # Fetch opinion details for top hits, respecting request budget
    hits_list = list(all_hits.values())[:5]
    cases_text = ""
    for hit in hits_list:
        cases_text += f"\n--- {hit.case_name} ---\n"
        cases_text += f"Court: {hit.court}\n"
        cases_text += f"Date: {hit.date_filed}\n"
        cases_text += f"Citation: {hit.citation}\n"
        cases_text += f"Snippet: {hit.snippet[:1000]}\n"

        # Try to get opinion detail for more context
        if hit.opinion_id and request_count < MAX_REQUESTS_PER_AGENT:
            try:
                request_count += 1
                opinion = await cl_client.get_opinion(hit.opinion_id)
                if opinion and opinion.opinion_text:
                    cases_text += f"Opinion excerpt: {opinion.opinion_text[:2000]}\n"
            except Exception as e:
                logger.warning(f"Failed to fetch opinion for cluster {hit.cluster_id}: {e}")

    logger.info(f"Caselaw agent for {statute.code} {statute.section}: {request_count} requests used")

    # Step 3: Ask Claude to evaluate results
    eval_prompt = CASELAW_EVALUATE_USER.format(
        code=statute.code,
        section=statute.section,
        title=statute.title,
        issue_label=issue.label,
        issue_description=issue.description,
        relevant_facts="\n".join(f"- {f}" for f in issue.relevant_facts),
        cases_text=cases_text,
    )

    try:
        evaluation = await claude.generate_json(CASELAW_EVALUATE_SYSTEM, eval_prompt)
    except Exception as e:
        logger.error(f"Case law evaluation failed for {statute.code} {statute.section}: {e}")
        return []

    # Convert evaluations to CaseLawResults
    results: list[CaseLawResult] = []
    for ev in evaluation.get("evaluations", []):
        if not ev.get("is_relevant", False):
            continue
        if ev.get("confidence", 0) < 0.3:
            continue

        # Find the URL from our search hits
        url = ""
        for hit in hits_list:
            if hit.case_name == ev.get("case_name"):
                url = f"{CL_BASE}{hit.absolute_url}" if hit.absolute_url else ""
                break

        results.append(
            CaseLawResult(
                case_name=ev.get("case_name", ""),
                citation=ev.get("citation", ""),
                court=ev.get("court", ""),
                date_filed=ev.get("date_filed", ""),
                url=url,
                snippet=ev.get("snippet", ""),
                relevance_summary=ev.get("relevance_summary", ""),
                related_statutes=ev.get("related_statutes", []),
                confidence=ev.get("confidence", 0.5),
                source_issue_id=issue.id,
            )
        )

    # Return top 2 by confidence
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results[:2]
