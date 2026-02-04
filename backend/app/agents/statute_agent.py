"""Wave 1: Statute sub-agent.

Each agent gets one issue slice + full fact pattern.
Two-step tool-use pattern:
1. LLM generates search queries
2. Python executes searches against leginfo
3. LLM evaluates results
"""

import json
import logging
from dataclasses import dataclass

MAX_REQUESTS_PER_AGENT = 5

from app.models.schemas import LegalIssue, FactPattern, StatuteResult
from app.services.claude_client import ClaudeClient
from app.services.leginfo_scraper import (
    lookup_section_cached,
    keyword_search,
    LegInfoSection,
    LegInfoSearchResult,
)
from app.agents.prompts import (
    STATUTE_AGENT_SYSTEM,
    STATUTE_AGENT_USER,
    STATUTE_EVALUATE_SYSTEM,
    STATUTE_EVALUATE_USER,
)

logger = logging.getLogger(__name__)


async def run_statute_agent(
    issue: LegalIssue,
    fact_pattern: FactPattern,
    claude: ClaudeClient,
) -> list[StatuteResult]:
    """Run a statute research agent for a single issue slice.

    Args:
        issue: The legal issue to research
        fact_pattern: The full fact pattern for context
        claude: Claude API client

    Returns:
        List of up to 2 StatuteResult candidates.
    """
    # Step 1: Ask Claude to generate search queries
    user_prompt = STATUTE_AGENT_USER.format(
        issue_label=issue.label,
        issue_description=issue.description,
        relevant_facts="\n".join(f"- {f}" for f in issue.relevant_facts),
        fact_summary=fact_pattern.summary,
    )

    try:
        search_plan = await claude.generate_json(STATUTE_AGENT_SYSTEM, user_prompt)
    except Exception as e:
        logger.error(f"Statute agent query generation failed for {issue.label}: {e}")
        return []

    # Step 2: Execute searches (capped at MAX_REQUESTS_PER_AGENT external requests)
    found_sections: dict[str, LegInfoSection] = {}
    request_count = 0

    # Direct lookups
    for lookup in search_plan.get("specific_lookups", []):
        if request_count >= MAX_REQUESTS_PER_AGENT:
            logger.info(f"Statute agent hit request limit ({MAX_REQUESTS_PER_AGENT}) for {issue.label}")
            break
        code = lookup.get("code", "")
        section = lookup.get("section", "")
        if code and section:
            request_count += 1
            result = await lookup_section_cached(code, section)
            if result:
                key = f"{result.code}:{result.section}"
                found_sections[key] = result

    # Keyword searches
    for query in search_plan.get("keyword_queries", [])[:5]:
        if request_count >= MAX_REQUESTS_PER_AGENT:
            break
        try:
            request_count += 1
            search_results = await keyword_search(query, max_results=5)
            for sr in search_results:
                if request_count >= MAX_REQUESTS_PER_AGENT:
                    break
                key = f"{sr.code}:{sr.section}"
                if key not in found_sections:
                    # Fetch full text for search results
                    request_count += 1
                    full_section = await lookup_section_cached(sr.code, sr.section)
                    if full_section:
                        found_sections[key] = full_section
        except Exception as e:
            logger.warning(f"Keyword search failed for '{query}': {e}")

    logger.info(f"Statute agent for {issue.label}: {request_count} requests used")

    if not found_sections:
        logger.info(f"No statutes found for issue {issue.label}")
        return []

    # Step 3: Ask Claude to evaluate results
    statutes_text = ""
    for key, sec in found_sections.items():
        statutes_text += f"\n--- {sec.code} Section {sec.section} ---\n"
        statutes_text += f"Title: {sec.title}\n"
        statutes_text += f"Text: {sec.full_text[:2000]}\n"

    eval_prompt = STATUTE_EVALUATE_USER.format(
        issue_label=issue.label,
        issue_description=issue.description,
        relevant_facts="\n".join(f"- {f}" for f in issue.relevant_facts),
        statutes_text=statutes_text,
    )

    try:
        evaluation = await claude.generate_json(STATUTE_EVALUATE_SYSTEM, eval_prompt)
    except Exception as e:
        logger.error(f"Statute evaluation failed for {issue.label}: {e}")
        return []

    # Convert evaluations to StatuteResults
    results: list[StatuteResult] = []
    for ev in evaluation.get("evaluations", []):
        if not ev.get("is_relevant", False):
            continue
        if ev.get("confidence", 0) < 0.3:
            continue

        code = ev.get("code", "")
        section = ev.get("section", "")
        key = f"{code}:{section}"
        sec = found_sections.get(key)

        results.append(
            StatuteResult(
                code=code,
                section=section,
                title=ev.get("title", sec.title if sec else ""),
                full_text=sec.full_text if sec else "",
                url=sec.url if sec else "",
                relevance_summary=ev.get("relevance_summary", ""),
                case_snippet=ev.get("case_snippet", ""),
                confidence=ev.get("confidence", 0.5),
                source_issue_id=issue.id,
            )
        )

    # Return top 2 by confidence
    results.sort(key=lambda r: r.confidence, reverse=True)
    return results[:2]
