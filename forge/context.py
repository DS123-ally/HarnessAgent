from dataclasses import dataclass
import json
from typing import Any


@dataclass
class ContextConfig:
    max_context_tokens: int = 16_000
    reserve_response_tokens: int = 4_000
    recent_turns: int = 8
    max_tool_output_chars: int = 12_000


class ContextAssembler:
    def __init__(self, config: ContextConfig | None = None):
        self.config = config or ContextConfig()

    def estimate_tokens(self, value: Any) -> int:
        if isinstance(value, str):
            text = value
        else:
            text = json.dumps(
                value,
                ensure_ascii=False,
                default=str,
            )

        return max(1, len(text) // 4)

    def input_budget(self) -> int:
        return (
            self.config.max_context_tokens
            - self.config.reserve_response_tokens
        )

    def truncate_tool_output(self, content: str) -> str:
        limit = self.config.max_tool_output_chars

        if len(content) <= limit:
            return content

        removed = len(content) - limit

        return (
            content[:limit]
            + f"\n\n[Tool output truncated: {removed} characters removed]"
        )

    def _sanitize_message(self, message: dict) -> dict:
        message = message.copy()

        if message.get("role") == "tool":
            content = message.get("content", "")

            if isinstance(content, str):
                message["content"] = self.truncate_tool_output(content)

        return message

    def _split_turns(self, history: list[dict]) -> list[list[dict]]:
        turns = []
        current_turn = []

        for message in history:
            if message.get("role") == "user":
                if current_turn:
                    turns.append(current_turn)

                current_turn = [message]

            else:
                current_turn.append(message)

        if current_turn:
            turns.append(current_turn)

        return turns

    def get_recent_history(self, history: list[dict]) -> list[dict]:
        turns = self._split_turns(history)

        recent_turns = turns[-self.config.recent_turns:]

        messages = []

        for turn in recent_turns:
            for message in turn:
                messages.append(
                    self._sanitize_message(message)
                )

        return messages

    def assemble(
        self,
        system_prompt: str,
        history: list[dict],
        summary: str | None = None,
        context_blocks: list[str] | None = None,
    ) -> list[dict]:

        messages = [
            {
                "role": "system",
                "content": system_prompt,
            }
        ]

        # AGENTS.md, @file context, etc.
        if context_blocks:
            for block in context_blocks:
                messages.append(
                    {
                        "role": "system",
                        "content": block,
                    }
                )

        # Summary of older conversation
        if summary:
            messages.append(
                {
                    "role": "system",
                    "content": (
                        "Summary of earlier conversation:\n\n"
                        + summary
                    ),
                }
            )

        # Only recent conversation
        recent_history = self.get_recent_history(history)

        messages.extend(recent_history)

        return messages

    def context_usage(self, messages: list[dict]) -> dict:
        used = self.estimate_tokens(messages)
        budget = self.input_budget()

        return {
            "estimated_tokens": used,
            "input_budget": budget,
            "response_reserved": self.config.reserve_response_tokens,
            "over_budget": used > budget,
        }

    def enforce_budget(self, messages: list[dict]) -> list[dict]:
        budget = self.input_budget()

        # Already fits
        if self.estimate_tokens(messages) <= budget:
            return messages

        system_messages = [
            message
            for message in messages
            if message.get("role") == "system"
        ]

        history = [
            message
            for message in messages
            if message.get("role") != "system"
        ]

        # Split history into complete user turns
        turns = self._split_turns(history)

        selected_turns = []

        # Start from newest turn
        for turn in reversed(turns):
            candidate_turns = [turn] + selected_turns

            candidate_history = [
                message
                for selected_turn in candidate_turns
                for message in selected_turn
            ]

            candidate = system_messages + candidate_history

            if self.estimate_tokens(candidate) > budget:
                break

            selected_turns.insert(0, turn)

        final_history = [
            message
            for turn in selected_turns
            for message in turn
        ]

        return system_messages + final_history

    def get_old_history(self, history: list[dict]) -> list[dict]:
        turns = self._split_turns(history)

        if len(turns) <= self.config.recent_turns:
            return []

        old_turns = turns[:-self.config.recent_turns]

        return [
            message
            for turn in old_turns
            for message in turn
        ]

