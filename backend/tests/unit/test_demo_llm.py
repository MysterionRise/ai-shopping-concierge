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
            SystemMessage(
                content="You are a search intent extractor for a beauty product database."
            ),
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
    assert '{"results": []}' in result.content


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


async def test_demo_llm_astream_yields_chunks():
    """Verify _astream yields ChatGenerationChunks that reassemble to full response."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a friendly AI beauty and skincare concierge."),
        HumanMessage(content="Hello!"),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        assert hasattr(chunk, "content"), "Each chunk should have a content attribute"
        chunks.append(chunk.content)

    assert len(chunks) > 1, "Stream should yield multiple chunks, not one big response"
    reassembled = "".join(chunks)
    assert reassembled == expected_full


async def test_demo_llm_astream_single_word():
    """Verify streaming works for short single-word responses like triage intents."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="Classify the user's message into exactly one intent."),
        HumanMessage(content="Hello there!"),
    ]
    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    reassembled = "".join(chunks)
    assert reassembled == "general_chat"


async def test_astream_triage_product_search():
    """Streaming triage: product_search reassembles correctly."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="Classify the user's message into exactly one intent."),
        HumanMessage(content="Can you recommend a moisturizer?"),
    ]
    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    reassembled = "".join(chunks)
    assert reassembled == "product_search"


async def test_astream_triage_ingredient_check():
    """Streaming triage: ingredient_check reassembles correctly."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="Classify the user's message into exactly one intent."),
        HumanMessage(content="Is paraben safe for my skin?"),
    ]
    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    reassembled = "".join(chunks)
    assert reassembled == "ingredient_check"


async def test_astream_triage_routine_advice():
    """Streaming triage: routine_advice reassembles correctly."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="Classify the user's message into exactly one intent."),
        HumanMessage(content="What should my morning routine be?"),
    ]
    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    reassembled = "".join(chunks)
    assert reassembled == "routine_advice"


async def test_astream_search_intent_multiline():
    """Streaming search intent extractor produces multi-line response with all fields."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a search intent extractor for a beauty product database."),
        HumanMessage(content="I need a serum for dry skin"),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    assert len(chunks) > 1
    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert "product_type: serum" in reassembled
    assert "skin_type: dry" in reassembled


async def test_astream_search_intent_with_brand():
    """Streaming search intent extractor detects brand mentions."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a search intent extractor for a beauty product database."),
        HumanMessage(content="Find me a cerave moisturizer for oily skin"),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert "brand_preference: Cerave" in reassembled
    assert "skin_type: oily" in reassembled


async def test_astream_safety_checker():
    """Streaming safety checker yields multiple chunks that reassemble to SAFE response."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a safety checker for beauty products."),
        HumanMessage(content="Check these products for safety."),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    assert len(chunks) > 1
    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert '{"results": []}' in reassembled


async def test_astream_conversational_routine():
    """Streaming conversational routine response with Morning/Evening structure."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a friendly AI beauty and skincare concierge."),
        HumanMessage(content="What routine should I follow?"),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    assert len(chunks) > 1
    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert "Morning" in reassembled


async def test_astream_conversational_thanks():
    """Streaming thanks response."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a friendly AI beauty and skincare concierge."),
        HumanMessage(content="Thanks for the help!"),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    assert len(chunks) > 1
    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert "welcome" in reassembled.lower()


async def test_astream_conversational_ingredient_check():
    """Streaming ingredient question response."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a friendly AI beauty and skincare concierge."),
        HumanMessage(content="Is niacinamide safe for my skin?"),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    assert len(chunks) > 1
    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert "ingredient" in reassembled.lower()


async def test_astream_conversational_fallback():
    """Streaming fallback conversational response for unmatched messages."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a friendly AI beauty and skincare concierge."),
        HumanMessage(content="What can you do?"),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    assert len(chunks) > 1
    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert "happy to help" in reassembled.lower()


async def test_astream_default_fallback():
    """Streaming default fallback when system prompt matches no branch."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are an unknown system."),
        HumanMessage(content="Do something."),
    ]
    expected_full = llm.invoke(messages).content

    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    assert len(chunks) > 1
    reassembled = "".join(chunks)
    assert reassembled == expected_full
    assert "beauty concierge" in reassembled.lower()


async def test_astream_chunk_spacing():
    """Verify first chunk has no leading space and non-empty subsequent chunks each have one."""
    llm = DemoChatModel()
    messages = [
        SystemMessage(content="You are a safety checker for beauty products."),
        HumanMessage(content="Check safety."),
    ]
    chunks = []
    async for chunk in llm.astream(messages):
        chunks.append(chunk.content)

    # Filter to non-empty chunks (base class may append a trailing empty chunk)
    nonempty = [c for c in chunks if c]
    assert len(nonempty) > 1
    assert not nonempty[0].startswith(" "), "First chunk should not start with a space"
    for i, c in enumerate(nonempty[1:], start=1):
        assert c.startswith(" "), f"Chunk {i} should start with a space: {c!r}"
