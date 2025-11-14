# Architecture Documentation

## System Overview

The Personal AI Shopping Concierge is a multi-agent system built on an orchestrator-subagent architecture pattern. Each agent is a specialized autonomous component that handles a specific aspect of the shopping journey.

## Design Principles

### 1. Modularity
- Each agent is self-contained with clear responsibilities
- Agents communicate through standardized message formats
- Easy to add, remove, or replace agents

### 2. Autonomy with Oversight
- Agents make autonomous decisions within their domain
- Human-in-the-loop checkpoints for critical actions
- Configurable autonomy levels

### 3. Composability
- Agents can be combined in different workflows
- Tools are reusable across agents
- System can be extended to other domains

### 4. Observability
- Structured logging for all agent actions
- Status tracking throughout workflows
- Clear error messages and handling

## Core Components

### Base Agent Class

```python
class BaseAgent(ABC):
    """Abstract base for all agents."""

    def __init__(self, role, name, description, system_prompt, tools):
        self.role = role           # Agent's role in the system
        self.name = name           # Human-readable name
        self.system_prompt = prompt # Instructions for Claude
        self.tools = tools         # Available tools
        self.status = AgentStatus.IDLE
        self.client = Anthropic()  # Claude API client
```

**Key Methods:**
- `process(input_data)` - Main processing method (abstract)
- `_call_claude(messages)` - Interact with Claude API
- `validate_input(input_data)` - Input validation
- `get_status()` / `set_status()` - Status management

### Agent Lifecycle

```
IDLE → PROCESSING → COMPLETED
                  ↘ FAILED
```

1. **IDLE**: Agent waiting for input
2. **PROCESSING**: Agent actively working
3. **COMPLETED**: Task finished successfully
4. **FAILED**: Error occurred during processing

## Agent Details

### 1. Needs Analysis Agent

**Purpose**: Convert natural language into structured shopping goals

**Input:**
```python
{
    "user_message": "I need running shoes under $150",
    "conversation_history": []  # Optional
}
```

**Output:**
```python
{
    "ready": true,
    "product_category": "running shoes",
    "budget": {"min": 0, "max": 150},
    "must_have_features": ["cushioning", "breathable"],
    "nice_to_have_features": ["lightweight"],
    "constraints": ["under $150"],
    "use_case": "daily running",
    "confidence_level": "high"
}
```

**Workflow:**
1. Parse user message
2. Check if information is sufficient
3. If not: Ask clarifying questions
4. If yes: Generate structured criteria

### 2. Product Research Agent

**Purpose**: Find products matching criteria

**Input:**
```python
{
    "shopping_criteria": {...},  # From Needs Analysis
    "max_results": 10
}
```

**Output:**
```python
{
    "products": [
        {
            "product_id": "SHOE-001",
            "name": "Nike Pegasus 40",
            "price": 129.99,
            "rating": 4.5,
            "features": [...],
            ...
        }
    ],
    "result_count": 5,
    "analysis": "Found 5 matching products..."
}
```

**Tools Used:**
- `MockProductSearchTool` - Search product database

**Workflow:**
1. Extract search parameters from criteria
2. Query product database using tools
3. Filter results by requirements
4. Analyze relevance of results

### 3. Comparison Agent

**Purpose**: Analyze and rank products

**Input:**
```python
{
    "products": [...],
    "shopping_criteria": {...},
    "top_n": 3
}
```

**Output:**
```python
{
    "ranked_products": [
        {
            "product_id": "SHOE-001",
            "rank": 1,
            "score": 9.2,
            "rationale": "Best value for features",
            "pros": ["Great cushioning", "Under budget"],
            "cons": ["Limited colors"],
            "best_for": "Daily runners"
        }
    ],
    "comparison_summary": "...",
    "top_recommendation": {...},
    "alternatives": [...]
}
```

**Workflow:**
1. Evaluate each product against criteria
2. Calculate scores based on multiple factors
3. Rank products
4. Generate explanations and rationale

**Scoring Factors:**
- Value for money (price vs features)
- Quality indicators (ratings, reviews)
- Feature completeness
- Brand reputation

### 4. Deal-Finding Agent

**Purpose**: Find discounts and best prices

**Input:**
```python
{
    "products": [...],
    "top_product": {...}  # Optional
}
```

**Output:**
```python
{
    "deals": [
        {
            "product_id": "SHOE-001",
            "current_price": 129.99,
            "coupons": ["NIKE10 - 10% off"],
            "savings_potential": {
                "amount": 13.00,
                "percentage": 10.0,
                "final_price": 116.99
            },
            "price_history": {...}
        }
    ],
    "summary": "Great deals available...",
    "best_deal": {...}
}
```

**Tools Used:**
- `MockCouponTool` - Find available coupons
- `MockPriceHistoryTool` - Get price trends

**Workflow:**
1. For each product:
   - Check for coupons
   - Get price history
   - Calculate savings potential
2. Identify best overall deal
3. Generate summary and recommendations

### 5. Transaction Agent

**Purpose**: Handle checkout and purchases

**Actions:**
- `prepare` - Create order summary for approval
- `execute` - Process purchase (requires approval)

**Input (Prepare):**
```python
{
    "action": "prepare",
    "products": [...],
    "shipping_address": {...}
}
```

**Output (Prepare):**
```python
{
    "order_summary": {
        "items": [...],
        "subtotal": 129.99,
        "tax": 10.40,
        "shipping": 0.00,
        "total": 140.39
    },
    "requires_approval": true,
    "approval_message": "Please review and confirm..."
}
```

**Input (Execute):**
```python
{
    "action": "execute",
    "products": [...],
    "shipping_address": {...},
    "payment_method": "credit_card",
    "user_approved": true  # REQUIRED
}
```

**Output (Execute):**
```python
{
    "success": true,
    "order_id": "ORD-123456",
    "confirmation_text": "...",
    "tracking_number": "...",
    "estimated_delivery": "3-5 business days"
}
```

**Tools Used:**
- `MockCheckoutTool` - Process transactions

**Safety Features:**
- Requires explicit `user_approved=true`
- Shows complete order summary before execution
- All costs clearly itemized
- Uses sandbox environment for testing

## Data Flow

### End-to-End Shopping Flow

```
User Input
    ↓
[Needs Analysis Agent]
    ↓ (structured criteria)
[Product Research Agent]
    ↓ (product list)
[Comparison Agent]
    ↓ (ranked recommendations)
[Deal-Finding Agent]
    ↓ (best prices/deals)
[Transaction Agent - Prepare]
    ↓ (order summary)
[User Approval] ← Human-in-the-loop
    ↓ (approval)
[Transaction Agent - Execute]
    ↓
Order Confirmation
```

### Message Format

All agents communicate using standardized messages:

```python
class Message(BaseModel):
    id: str                    # Unique ID
    sender: str                # Agent name
    recipient: str             # Target agent/user
    content: str               # Message content
    metadata: Dict[str, Any]   # Additional data
    timestamp: datetime        # When sent
```

### Agent Response Format

```python
class AgentResponse(BaseModel):
    agent_role: AgentRole      # Which agent
    status: AgentStatus        # Success/failure
    output: Dict[str, Any]     # Result data
    messages: List[Message]    # Messages generated
    errors: List[str]          # Any errors
    metadata: Dict[str, Any]   # Additional info
```

## Tool System

Tools extend agent capabilities to interact with external systems.

### Tool Interface

```python
class Tool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """Execute the tool."""
        pass
```

### Available Tools (Phase 1)

1. **MockProductSearchTool**
   - Search products by category, price, features
   - Returns product details

2. **MockCouponTool**
   - Find coupons by brand
   - Returns available deals

3. **MockPriceHistoryTool**
   - Get historical prices
   - Analyze price trends

4. **MockCheckoutTool**
   - Simulate purchase
   - Calculate totals
   - Generate order confirmation

## Configuration

### Settings Management

Configuration is managed through Pydantic settings:

```python
class Settings(BaseSettings):
    # Anthropic API
    anthropic_api_key: str
    claude_model: str = "claude-3-5-sonnet-20241022"
    max_tokens: int = 4096
    temperature: float = 0.7

    # Agent Config
    max_iterations: int = 5
    timeout_seconds: int = 30

    # Mock Data
    use_mock_data: bool = True
```

Loaded from environment variables or `.env` file.

## Error Handling

### Error Categories

1. **Validation Errors**
   - Invalid input format
   - Missing required fields
   - Type mismatches

2. **Processing Errors**
   - Claude API failures
   - Tool execution errors
   - Timeout errors

3. **Business Logic Errors**
   - No products found
   - Insufficient information
   - Transaction declined

### Error Response Format

```python
AgentResponse(
    status=AgentStatus.FAILED,
    output={},
    errors=["Error message here"],
    metadata={"error_type": "validation"}
)
```

## Logging and Observability

### Structured Logging

All agents use structured logging:

```python
self.logger.info(
    "processing_request",
    agent=self.name,
    input_size=len(input_data),
    user_id=user_id
)
```

### Log Levels

- **DEBUG**: Detailed diagnostic info
- **INFO**: Normal operations
- **WARNING**: Unusual but handled situations
- **ERROR**: Error conditions
- **CRITICAL**: System failures

## Security Considerations

### API Key Management
- Stored in environment variables
- Never committed to version control
- Rotated regularly

### Input Validation
- All inputs validated before processing
- Type checking with Pydantic
- Sanitization of user inputs

### Transaction Safety
- Explicit user approval required
- All costs shown before execution
- Sandbox environment for testing
- Rate limiting on API calls

## Performance Considerations

### Async Operations
- All agent processing is async
- Parallel tool execution where possible
- Non-blocking Claude API calls

### Caching Strategy
- Cache product search results
- Memoize expensive computations
- Claude response caching (future)

### Optimization Targets
- Agent response time: < 5s
- End-to-end flow: < 30s
- Support 10+ concurrent users

## Testing Strategy

### Unit Tests
- Test each agent in isolation
- Mock Claude API responses
- Mock tool executions
- 80%+ coverage target

### Integration Tests
- Test agent interactions
- Full workflow testing
- Real tool integration (future)

### Test Structure
```
tests/
├── unit/
│   ├── test_needs_analysis.py
│   ├── test_product_research.py
│   ├── test_comparison.py
│   ├── test_deal_finding.py
│   └── test_transaction.py
├── integration/
│   └── test_workflows.py
└── fixtures/
    └── mock_data.py
```

## Future Enhancements

### Phase 2+
- Real API integrations (Amazon, Walmart, etc.)
- Vector database for semantic search
- User preference memory
- Conversation context management
- Multi-session support

### Advanced Features
- Voice interface
- Image-based product search
- Predictive shopping recommendations
- Supply chain integration
- Inventory management

## Deployment Architecture

### Current (Phase 1)
- Single Python application
- Environment-based configuration
- Mock data and tools

### Future (Production)
```
┌─────────────┐
│   Frontend  │ (React/Streamlit)
└──────┬──────┘
       │
┌──────▼──────┐
│  API Layer  │ (FastAPI)
└──────┬──────┘
       │
┌──────▼──────┐
│ Orchestrator│
└──────┬──────┘
       │
┌──────▼──────────────────┐
│ Agent Pool (5 agents)   │
└──────┬──────────────────┘
       │
┌──────▼──────────────────┐
│ External Services       │
│ - Claude API            │
│ - Product APIs          │
│ - Payment Gateway       │
│ - Vector DB             │
└─────────────────────────┘
```

## Extensibility

### Adding New Agents

1. Inherit from `BaseAgent`
2. Implement `process()` method
3. Define input/output schemas
4. Create prompt template
5. Add tests
6. Update orchestrator

### Adding New Tools

1. Inherit from `Tool`
2. Implement `execute()` method
3. Add to agent's tool list
4. Add tests
5. Document usage

### Adapting to Other Domains

The architecture is domain-agnostic:
- **Publishing**: Content research, fact-checking, summarization
- **Patents**: Prior art search, claim analysis
- **Education**: Personalized tutoring, content curation
- **Healthcare**: Symptom analysis, treatment research

## Conclusion

This architecture provides a solid foundation for building sophisticated multi-agent AI systems. The modular design, clear separation of concerns, and emphasis on safety make it suitable for real-world applications while remaining flexible enough to evolve with requirements.
