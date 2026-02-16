from langchain_core.messages import HumanMessage, SystemMessage

from app.core.llm import DemoChatModel


def test_demo_llm_triage_product_search():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="Classify the user's message into exactly one intent."),
            HumanMessage(content="Can you recommend a moisturizer?"),
        ]
    )
    assert result.content == "product_search"


def test_demo_llm_triage_general_chat():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="Classify the user's message into exactly one intent."),
            HumanMessage(content="Hello there!"),
        ]
    )
    assert result.content == "general_chat"


def test_demo_llm_triage_ingredient_check():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="Classify the user's message into exactly one intent."),
            HumanMessage(content="Is paraben safe for my skin?"),
        ]
    )
    assert result.content == "ingredient_check"


def test_demo_llm_triage_routine_advice():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="Classify the user's message into exactly one intent."),
            HumanMessage(content="What should my morning routine be?"),
        ]
    )
    assert result.content == "routine_advice"


def test_demo_llm_search_intent():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="You are a search intent extractor for a beauty product database."),
            HumanMessage(content="I need a serum for dry skin"),
        ]
    )
    assert "serum" in result.content
    assert "dry" in result.content


def test_demo_llm_safety_checker():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="You are a safety checker for beauty products."),
            HumanMessage(content="Check these products for safety."),
        ]
    )
    assert "SAFE" in result.content


def test_demo_llm_conversational_greeting():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="You are a friendly AI beauty and skincare concierge."),
            HumanMessage(content="Hello!"),
        ]
    )
    assert "Beauty Concierge" in result.content


def test_demo_llm_conversational_routine():
    llm = DemoChatModel()
    result = llm.invoke(
        [
            SystemMessage(content="You are a friendly AI beauty and skincare concierge."),
            HumanMessage(content="What routine should I follow?"),
        ]
    )
    assert "Morning" in result.content or "routine" in result.content.lower()


def test_demo_llm_llm_type():
    llm = DemoChatModel()
    assert llm._llm_type == "demo"


async def test_demo_llm_async():
    llm = DemoChatModel()
    result = await llm.ainvoke(
        [
            SystemMessage(content="Classify the user's message into exactly one intent."),
            HumanMessage(content="Find me a cleanser"),
        ]
    )
    assert result.content == "product_search"
