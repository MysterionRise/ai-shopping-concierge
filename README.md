# Personal AI Shopping Concierge 🛍️

A sophisticated multi-agent generative AI system that autonomously assists users in finding and purchasing products in retail scenarios. Built with Claude (Anthropic) and Python.

[![CI Pipeline](https://github.com/your-org/agentic-approach-in-genai/actions/workflows/ci.yml/badge.svg)](https://github.com/your-org/agentic-approach-in-genai/actions/workflows/ci.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

The Personal AI Shopping Concierge demonstrates practical agentic AI capabilities through a team of specialized agents that work together to handle the entire customer shopping journey - from understanding needs to finalizing purchases.

### Key Features

- **Multi-Agent Architecture**: Five specialized agents working in concert
- **Natural Language Interface**: Conversational shopping experience
- **Autonomous Decision Making**: Agents collaborate and iterate to achieve goals
- **Human-in-the-Loop**: Critical checkpoints for user approval
- **Modular Design**: Easily extensible to other domains

## 🏗️ Architecture

The system consists of five specialized agents:

### 1. **Needs Analysis Agent** 🎯
- Engages users in natural language
- Clarifies requirements through follow-up questions
- Converts conversations to structured shopping goals

### 2. **Product Research Agent** 🔍
- Searches across product databases
- Filters based on criteria
- Parses product details, reviews, and ratings

### 3. **Comparison & Recommendation Agent** ⚖️
- Analyzes and compares products
- Ranks options by value, quality, features
- Explains trade-offs in plain language

### 4. **Deal-Finding Agent** 💰
- Checks for discounts and coupons
- Analyzes price history and trends
- Identifies best savings opportunities

### 5. **Transaction Agent** 🛒
- Prepares order summaries
- Handles checkout process (sandboxed)
- Requires explicit user approval

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for detailed architecture documentation.

## 🚀 Quick Start

### Prerequisites

- Python 3.11 or higher
- Anthropic API key ([Get one here](https://console.anthropic.com/))

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-org/agentic-approach-in-genai.git
   cd agentic-approach-in-genai
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # For development
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
   ```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test categories
pytest tests/unit -v
pytest tests/integration -v

# Run with coverage report
pytest --cov=src/shopping_concierge --cov-report=html
```

### Code Quality

```bash
# Format code
black src tests
isort src tests

# Lint
flake8 src tests

# Type check
mypy src
```

## 📖 Usage Example

```python
import asyncio
from shopping_concierge.agents import (
    NeedsAnalysisAgent,
    ProductResearchAgent,
    ComparisonAgent,
)

async def main():
    # Step 1: Understand user needs
    needs_agent = NeedsAnalysisAgent()
    needs_response = await needs_agent.process({
        "user_message": "I need running shoes under $150"
    })

    # Step 2: Search for products
    research_agent = ProductResearchAgent()
    products_response = await research_agent.process({
        "shopping_criteria": needs_response.output
    })

    # Step 3: Compare and recommend
    comparison_agent = ComparisonAgent()
    recommendations = await comparison_agent.process({
        "products": products_response.output["products"],
        "shopping_criteria": needs_response.output,
        "top_n": 3
    })

    print(recommendations.output)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📁 Project Structure

```
agentic-approach-in-genai/
├── src/
│   └── shopping_concierge/
│       ├── agents/           # Agent implementations
│       │   ├── base.py       # Base agent classes
│       │   ├── needs_analysis.py
│       │   ├── product_research.py
│       │   ├── comparison.py
│       │   ├── deal_finding.py
│       │   └── transaction.py
│       ├── tools/            # Tools for agents
│       │   └── mock_tools.py # Mock API implementations
│       ├── config/           # Configuration
│       │   └── settings.py
│       └── prompts/          # Prompt templates
│           └── templates.py
├── tests/
│   ├── unit/                # Unit tests
│   ├── integration/         # Integration tests
│   └── fixtures/            # Test fixtures
├── docs/                    # Documentation
├── .github/
│   └── workflows/          # CI/CD pipelines
├── pyproject.toml          # Project configuration
├── requirements.txt        # Production dependencies
├── requirements-dev.txt    # Development dependencies
└── README.md

```

## 🧪 Phase 1 - Implementation Status

### ✅ Completed

- [x] Core agent base classes and interfaces
- [x] All 5 agent implementations
- [x] Mock tool implementations for testing
- [x] Comprehensive unit test suite (80%+ coverage)
- [x] CI/CD pipeline with GitHub Actions
- [x] Project documentation
- [x] Prompt engineering for each agent
- [x] Error handling and validation

### 🎯 Success Criteria Met

- ✅ All agents respond correctly to test inputs
- ✅ Tool integration works with mock data
- ✅ 80%+ test coverage achieved
- ✅ CI pipeline configured and ready
- ✅ Clear documentation for handoff

## 🛣️ Roadmap

### Phase 2: Orchestrator & Dialogue (Weeks 3-4)
- [ ] Implement orchestrator with state machine
- [ ] Build conversation flow management
- [ ] Create Streamlit UI
- [ ] Add integration tests

### Phase 3: Integration & Memory (Weeks 5-6)
- [ ] Integrate vector database for semantic search
- [ ] Add user preference memory
- [ ] Implement real product catalog
- [ ] Performance optimization

### Phase 4: Testing & Refinement (Week 7)
- [ ] Expand to 90%+ test coverage
- [ ] User acceptance testing
- [ ] Security audit
- [ ] Performance tuning

### Phase 5: Demo Preparation (Week 8)
- [ ] Create demo scenarios
- [ ] Record walkthrough video
- [ ] Deploy to staging
- [ ] Prepare presentation

## 🔧 Configuration

Configuration is managed through environment variables. See `.env.example` for all available options:

```env
# Anthropic API
ANTHROPIC_API_KEY=your_key_here
CLAUDE_MODEL=claude-3-5-sonnet-20241022

# Agent Settings
MAX_ITERATIONS=5
TIMEOUT_SECONDS=30

# Mock Data (for testing)
USE_MOCK_DATA=true
```

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 Development

### Setting Up Pre-commit Hooks

```bash
pre-commit install
```

This will run code quality checks before each commit.

### Running the Full CI Pipeline Locally

```bash
# Code quality
black --check src tests
isort --check src tests
flake8 src tests

# Tests
pytest --cov=src/shopping_concierge

# Security
bandit -r src
```

## 📚 Documentation

- [Architecture Guide](docs/ARCHITECTURE.md) - Detailed system architecture
- [Project Plan](PROJECT_PLAN.md) - Comprehensive project plan
- [API Documentation](docs/API.md) - API reference (coming soon)

## 🔒 Security

- API keys are managed through environment variables
- All user inputs are validated
- Transactions require explicit user approval
- Regular security scans in CI pipeline

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [Anthropic Claude](https://www.anthropic.com/claude)
- Inspired by multi-agent AI research and retail innovation trends
- Thanks to the open-source community for excellent tools

## 📞 Contact

- **Project Lead**: [Your Name]
- **GitHub Issues**: [Issue Tracker](https://github.com/your-org/agentic-approach-in-genai/issues)
- **Email**: your.email@example.com

---

**Note**: This is Phase 1 implementation with mock data. Real API integrations and advanced features will be added in subsequent phases.
