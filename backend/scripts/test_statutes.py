#!/usr/bin/env python3
"""Isolated test runner for the statute lookup process.

Usage:
    cd backend
    source .venv/bin/activate
    python scripts/test_statutes.py test_cases/palsgraf.json
"""

import asyncio
import json
import logging
import sys
from pathlib import Path

# Ensure the backend package is importable when running from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Load .env before importing app modules (pydantic-settings reads it, but
# dotenv ensures it's available even if pydantic-settings isn't first).
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from app.agents.prompts import FACT_PATTERN_SYSTEM, FACT_PATTERN_USER
from app.agents.statute_agent import run_statute_agent
from app.models.schemas import FactPattern, LegalIssue, StatuteResult
from app.services.claude_client import ClaudeClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(name)s %(levelname)s  %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("test_statutes")


# ── helpers ──────────────────────────────────────────────────────────────


def print_fact_pattern(fp: FactPattern) -> None:
    print("\n=== Fact Pattern ===")
    print(f"Summary: {fp.summary}")
    print(f"Parties: {', '.join(fp.parties)}")
    print(f"Issues ({len(fp.issues)}):")
    for i, iss in enumerate(fp.issues, 1):
        print(f"  {i}. [{iss.id}] {iss.label} — {iss.description[:80]}...")


def print_statute_results(results: list[StatuteResult]) -> None:
    if not results:
        print("  (no statutes found)")
        return
    for r in results:
        print(f"  • {r.code} § {r.section} — {r.title}")
        print(f"    confidence: {r.confidence:.2f}")
        print(f"    relevance:  {r.relevance_summary[:120]}")
        print()


# ── core logic ───────────────────────────────────────────────────────────


async def extract_fact_pattern(text: str, claude: ClaudeClient) -> FactPattern:
    """Call Claude to extract a FactPattern from raw case text."""
    user_prompt = FACT_PATTERN_USER.format(case_text=text)
    fp_data = await claude.generate_json(FACT_PATTERN_SYSTEM, user_prompt)

    return FactPattern(
        summary=fp_data.get("summary", ""),
        parties=fp_data.get("parties", []),
        issues=[
            LegalIssue(**issue_data)
            for issue_data in fp_data.get("issues", [])[:4]
        ],
        jurisdiction=fp_data.get("jurisdiction", "California"),
    )


def hydrate_fact_pattern(data: dict) -> FactPattern:
    """Build a FactPattern from a pre-extracted JSON object."""
    return FactPattern(
        summary=data["summary"],
        parties=data["parties"],
        issues=[LegalIssue(**iss) for iss in data["issues"][:4]],
        jurisdiction=data.get("jurisdiction", "California"),
    )


async def main() -> None:
    if len(sys.argv) < 2:
        print("Usage: python scripts/test_statutes.py <test_case.json>")
        sys.exit(1)

    test_path = Path(sys.argv[1])
    if not test_path.exists():
        print(f"File not found: {test_path}")
        sys.exit(1)

    print(f"\n=== Loading test case: {test_path} ===")
    with open(test_path) as f:
        test_data = json.load(f)

    claude = ClaudeClient()

    # ── Step 1: obtain fact pattern ──────────────────────────────────
    if "fact_pattern" in test_data:
        print("Mode: pre-extracted fact pattern (skipping Claude extraction)")
        fact_pattern = hydrate_fact_pattern(test_data["fact_pattern"])
    elif "text" in test_data:
        print("Mode: raw text -> extracting fact pattern via Claude...")
        fact_pattern = await extract_fact_pattern(test_data["text"], claude)
    else:
        print("Error: JSON must contain either 'text' or 'fact_pattern' key")
        sys.exit(1)

    print_fact_pattern(fact_pattern)

    # ── Step 2: run statute agent for each issue (sequential) ────────
    all_statutes: list[StatuteResult] = []

    for issue in fact_pattern.issues:
        print(f'\n=== Statute agent: issue "{issue.label}" ===')
        results = await run_statute_agent(issue, fact_pattern, claude)
        print_statute_results(results)
        all_statutes.extend(results)

    # ── Step 3: final summary ────────────────────────────────────────
    print(f"\n=== DONE — {len(all_statutes)} total statutes found ===")
    print(
        json.dumps(
            [s.model_dump() for s in all_statutes],
            indent=2,
            default=str,
        )
    )


if __name__ == "__main__":
    asyncio.run(main())
