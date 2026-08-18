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
        """
        Rough token estimation.

        For now:
        ~4 characters = 1 token.
        """

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
        """
        Context space available for input after
        reserving space for the model response.
        """

        return (
            self.config.max_context_tokens
            - self.config.reserve_response_tokens
        )

    def truncate_tool_output(self, content: str) -> str:
        """
        Prevent huge tool outputs from consuming
        the entire model context.
        """

        limit = self.config.max_tool_output_chars

        if len(content) <= limit:
            return content

        removed = len(content) - limit

        return (
            content[:limit]
            + f"\n\n[Tool output truncated: {removed} characters removed]"
        )

    def _sanitize_message(self, message: dict) -> dict:
        """
        Create a safe copy of a message before
        sending it to the model.
        """

        message = message.copy()

        if message.get("role") == "tool":
            content = message.get("content", "")

            if isinstance(content, str):
                message["content"] = self.truncate_tool_output(
                    content
                )

        return message

    def _split_turns(
        self,
        history: list[dict],
    ) -> list[list[dict]]:
        """
        Split conversation history into complete
        user conversation turns.

        Example:

        user
        assistant
        tool
        assistant

        = one turn
        """

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

    def get_recent_history(
        self,
        history: list[dict],
    ) -> list[dict]:
        """
        Return only the most recent conversation
        turns defined by recent_turns.
        """

        turns = self._split_turns(history)

        recent_turns = turns[
            -self.config.recent_turns:
        ]

        messages = []

        for turn in recent_turns:
            for message in turn:
                messages.append(
                    self._sanitize_message(message)
                )

        return messages

    def get_old_history(
        self,
        history: list[dict],
    ) -> list[dict]:
        """
        Return conversation turns that are older
        than the recent-turn window.
        """

        turns = self._split_turns(history)

        if len(turns) <= self.config.recent_turns:
            return []

        old_turns = turns[
            :-self.config.recent_turns
        ]

        return [
            message
            for turn in old_turns
            for message in turn
        ]

    def get_unsummarized_old_history(
        self,
        history: list[dict],
        summarized_turns: int,
    ) -> tuple[list[dict], int]:
        """
        Return only old turns that have not
        already been added to the summary.

        Also returns the new count of summarized
        turns.
        """

        turns = self._split_turns(history)

        old_turn_count = max(
            0,
            len(turns) - self.config.recent_turns,
        )

        # Nothing new became old
        if summarized_turns >= old_turn_count:
            return [], summarized_turns

        new_old_turns = turns[
            summarized_turns:old_turn_count
        ]

        messages = [
            message
            for turn in new_old_turns
            for message in turn
        ]

        return messages, old_turn_count

    def assemble(
        self,
        system_prompt: str,
        history: list[dict],
        summary: str | None = None,
        context_blocks: list[str] | None = None,
    ) -> list[dict]:
        """
        Assemble the final context that will
        eventually be sent to the model.
        """

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

        # Compact summary of older conversation
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

        recent_history = self.get_recent_history(
            history
        )

        messages.extend(recent_history)

        return messages

    def context_usage(
        self,
        messages: list[dict],
    ) -> dict:
        """
        Return context-budget information.
        """

        used = self.estimate_tokens(messages)
        budget = self.input_budget()

        return {
            "estimated_tokens": used,
            "input_budget": budget,
            "response_reserved": (
                self.config.reserve_response_tokens
            ),
            "over_budget": used > budget,
        }

    def enforce_budget(
        self,
        messages: list[dict],
    ) -> list[dict]:
        """
        Ensure model input stays inside the input
        token budget.

        Old conversation is removed by complete
        turns instead of individual messages.
        """

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

        turns = self._split_turns(history)

        selected_turns = []

        # Work backwards from the newest turn
        for turn in reversed(turns):

            candidate_turns = [
                turn,
                *selected_turns,
            ]

            candidate_history = [
                message
                for selected_turn in candidate_turns
                for message in selected_turn
            ]

            candidate = (
                system_messages
                + candidate_history
            )

            if self.estimate_tokens(candidate) > budget:
                break

            selected_turns.insert(
                0,
                turn,
            )

        final_history = [
            message
            for turn in selected_turns
            for message in turn
        ]

        return (
            system_messages
            + final_history
        )
