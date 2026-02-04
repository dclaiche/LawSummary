"""Anthropic Claude API wrapper.

Uses Claude Sonnet for all agents. Expects JSON output mode.
"""

import json
import logging

import anthropic

from app.config import settings

logger = logging.getLogger(__name__)

MODEL = "claude-sonnet-4-20250514"


class ClaudeClient:
    def __init__(self, api_key: str | None = None) -> None:
        self._client = anthropic.AsyncAnthropic(
            api_key=api_key or settings.anthropic_api_key,
        )

    async def generate_json(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> dict:
        """Generate a JSON response from Claude.

        Args:
            system_prompt: System instructions
            user_prompt: User message
            max_tokens: Maximum tokens in response

        Returns:
            Parsed JSON dict from Claude's response.
        """
        try:
            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )

            text = response.content[0].text

            # Try to extract JSON from the response
            # Claude sometimes wraps JSON in markdown code blocks
            if "```json" in text:
                text = text.split("```json")[1].split("```")[0]
            elif "```" in text:
                text = text.split("```")[1].split("```")[0]

            return json.loads(text.strip())

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Claude JSON response: {e}")
            logger.debug(f"Raw response: {text}")
            raise ValueError(f"Claude returned invalid JSON: {e}")
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise

    async def generate_text(
        self,
        system_prompt: str,
        user_prompt: str,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a text response from Claude.

        Args:
            system_prompt: System instructions
            user_prompt: User message
            max_tokens: Maximum tokens in response

        Returns:
            Text string from Claude's response.
        """
        try:
            response = await self._client.messages.create(
                model=MODEL,
                max_tokens=max_tokens,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            )
            return response.content[0].text
        except anthropic.APIError as e:
            logger.error(f"Claude API error: {e}")
            raise
