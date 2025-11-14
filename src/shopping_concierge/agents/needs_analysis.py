"""Needs Analysis Agent implementation."""

import json
from typing import Any, Dict

from .base import AgentResponse, AgentRole, AgentStatus, BaseAgent
from ..prompts.templates import get_agent_prompt


class NeedsAnalysisAgent(BaseAgent):
    """Agent responsible for understanding and clarifying user shopping needs."""

    def __init__(self) -> None:
        """Initialize Needs Analysis Agent."""
        super().__init__(
            role=AgentRole.NEEDS_ANALYSIS,
            name="Needs Analyzer",
            description="Understands and clarifies user shopping requirements",
            system_prompt=get_agent_prompt("needs_analysis"),
            tools=[],
        )

    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process user input to extract and structure shopping needs.

        Args:
            input_data: Dictionary containing:
                - user_message: User's shopping request
                - conversation_history: Optional previous messages

        Returns:
            AgentResponse with structured needs analysis
        """
        await self.validate_input(input_data)
        self.set_status(AgentStatus.PROCESSING)

        try:
            user_message = input_data.get("user_message", "")
            conversation_history = input_data.get("conversation_history", [])

            self.logger.info("analyzing_user_needs", message_length=len(user_message))

            # Build messages for Claude
            messages = []

            # Add conversation history
            for msg in conversation_history:
                messages.append({"role": msg["role"], "content": msg["content"]})

            # Add current user message with instruction to analyze
            analysis_instruction = f"""
User request: {user_message}

Please analyze this request and determine if you have enough information to create a structured shopping goal.

If you need more information, respond with a natural follow-up question.

If you have enough information, respond with a JSON object (and ONLY the JSON object) containing:
{{
    "ready": true,
    "product_category": "category of product",
    "budget": {{"min": 0, "max": 100}},
    "must_have_features": ["feature1", "feature2"],
    "nice_to_have_features": ["feature3"],
    "constraints": ["constraint1"],
    "use_case": "description of how product will be used",
    "confidence_level": "high"
}}

If you need more information, respond with:
{{
    "ready": false,
    "question": "Your follow-up question here"
}}
"""

            messages.append({"role": "user", "content": analysis_instruction})

            # Call Claude
            response = await self._call_claude(messages)

            # Parse response
            output = self._parse_response(response)

            self.set_status(AgentStatus.COMPLETED)

            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.COMPLETED,
                output=output,
                metadata={"input_message": user_message},
            )

        except Exception as e:
            self.logger.error("needs_analysis_error", error=str(e))
            self.set_status(AgentStatus.FAILED)
            return AgentResponse(
                agent_role=self.role,
                status=AgentStatus.FAILED,
                output={},
                errors=[str(e)],
            )

    def _parse_response(self, response: str) -> Dict[str, Any]:
        """
        Parse Claude's response into structured output.

        Args:
            response: Raw response from Claude

        Returns:
            Structured output dictionary
        """
        # Try to find JSON in the response
        try:
            # Look for JSON object in the response
            start_idx = response.find("{")
            end_idx = response.rfind("}") + 1

            if start_idx != -1 and end_idx > start_idx:
                json_str = response[start_idx:end_idx]
                parsed = json.loads(json_str)
                return parsed
            else:
                # No JSON found, treat as a question
                return {"ready": False, "question": response.strip()}

        except json.JSONDecodeError:
            # If JSON parsing fails, treat entire response as a question
            return {"ready": False, "question": response.strip()}

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data.

        Args:
            input_data: Input to validate

        Returns:
            True if valid

        Raises:
            ValueError: If input is invalid
        """
        await super().validate_input(input_data)

        if "user_message" not in input_data:
            raise ValueError("Input must contain 'user_message'")

        if not input_data["user_message"].strip():
            raise ValueError("User message cannot be empty")

        return True
