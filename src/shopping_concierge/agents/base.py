"""Base classes for all agents in the Shopping Concierge system."""

import uuid
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import structlog
from anthropic import Anthropic
from pydantic import BaseModel, Field

from ..config.settings import get_settings

logger = structlog.get_logger()


class AgentRole(str, Enum):
    """Enumeration of agent roles in the system."""

    NEEDS_ANALYSIS = "needs_analysis"
    PRODUCT_RESEARCH = "product_research"
    COMPARISON = "comparison"
    DEAL_FINDING = "deal_finding"
    TRANSACTION = "transaction"


class AgentStatus(str, Enum):
    """Agent execution status."""

    IDLE = "idle"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class Message(BaseModel):
    """Message exchanged between agents and users."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    content: str
    metadata: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class AgentResponse(BaseModel):
    """Structured response from an agent."""

    agent_role: AgentRole
    status: AgentStatus
    output: Dict[str, Any]
    messages: List[Message] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class Tool(ABC):
    """Abstract base class for tools that agents can use."""

    def __init__(self, name: str, description: str):
        """Initialize tool with name and description."""
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs: Any) -> Dict[str, Any]:
        """Execute the tool with given parameters."""
        pass


class BaseAgent(ABC):
    """Abstract base class for all agents."""

    def __init__(
        self,
        role: AgentRole,
        name: str,
        description: str,
        system_prompt: str,
        tools: Optional[List[Tool]] = None,
    ):
        """
        Initialize base agent.

        Args:
            role: The role this agent fulfills
            name: Human-readable name for the agent
            description: Description of agent's capabilities
            system_prompt: System prompt for Claude
            tools: List of tools available to this agent
        """
        self.role = role
        self.name = name
        self.description = description
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.status = AgentStatus.IDLE

        # Initialize settings and Claude client
        self.settings = get_settings()
        self.client = Anthropic(api_key=self.settings.anthropic_api_key)

        # Initialize logger
        self.logger = logger.bind(agent=self.name, role=self.role.value)

    @abstractmethod
    async def process(self, input_data: Dict[str, Any]) -> AgentResponse:
        """
        Process input and generate response.

        Args:
            input_data: Input data for the agent to process

        Returns:
            AgentResponse containing the agent's output
        """
        pass

    async def _call_claude(
        self,
        messages: List[Dict[str, str]],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
    ) -> str:
        """
        Call Claude API with messages.

        Args:
            messages: List of message dictionaries
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature

        Returns:
            Response text from Claude
        """
        self.logger.info("calling_claude", num_messages=len(messages))

        try:
            response = self.client.messages.create(
                model=self.settings.claude_model,
                max_tokens=max_tokens or self.settings.max_tokens,
                temperature=temperature or self.settings.temperature,
                system=self.system_prompt,
                messages=messages,
            )

            # Extract text from response
            text_content = ""
            for block in response.content:
                if hasattr(block, "text"):
                    text_content += block.text

            self.logger.info(
                "claude_response_received",
                response_length=len(text_content),
                usage=response.usage.model_dump() if response.usage else None,
            )

            return text_content

        except Exception as e:
            self.logger.error("claude_api_error", error=str(e))
            raise

    def _create_message(
        self, recipient: str, content: str, metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """
        Create a message from this agent.

        Args:
            recipient: Recipient identifier
            content: Message content
            metadata: Optional metadata

        Returns:
            Message object
        """
        return Message(
            sender=self.name,
            recipient=recipient,
            content=content,
            metadata=metadata or {},
        )

    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """
        Validate input data before processing.

        Args:
            input_data: Input data to validate

        Returns:
            True if valid, raises exception otherwise
        """
        if not isinstance(input_data, dict):
            raise ValueError("Input data must be a dictionary")
        return True

    def get_status(self) -> AgentStatus:
        """Get current agent status."""
        return self.status

    def set_status(self, status: AgentStatus) -> None:
        """Set agent status."""
        self.status = status
        self.logger.info("status_changed", new_status=status.value)
