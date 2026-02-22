from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.agents.graph import compile_graph
from app.api.routes import chat, conversations, health, memory, persona, products, users
from app.config import settings

structlog.configure(
    processors=[
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Beauty Concierge API")

    # Initialize LangGraph checkpointer
    checkpointer_cm = None
    checkpointer = None
    try:
        from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

        checkpointer_cm = AsyncPostgresSaver.from_conn_string(settings.checkpoint_db_url)
        checkpointer = await checkpointer_cm.__aenter__()
        await checkpointer.setup()
        logger.info("LangGraph checkpointer: AsyncPostgresSaver (Postgres)")
    except Exception as e:
        logger.warning("Postgres checkpointer failed, using MemorySaver", error=str(e))
        checkpointer_cm = None

    # Initialize LangMem store (AsyncPostgresStore for long-term memory)
    store_cm = None
    store = None
    try:
        from app.memory.langmem_config import get_store_context

        store_cm = get_store_context()
        store = await store_cm.__aenter__()
        await store.setup()
        app.state.store = store
        logger.info("LangMem store: AsyncPostgresStore (Postgres)")
    except Exception as e:
        logger.warning("LangMem store failed, memories disabled", error=str(e))
        app.state.store = None
        store_cm = None

    # Initialize PersonaMonitor
    app.state.persona_monitor = None
    if settings.persona_enabled:
        try:
            from app.core.database import async_session_factory
            from app.core.redis import get_redis_client
            from app.persona.monitor import MockPersonaScorer, PersonaMonitor

            persona_redis = get_redis_client()
            scorer = MockPersonaScorer() if settings.persona_scorer == "mock" else None
            app.state.persona_monitor = PersonaMonitor(
                redis_client=persona_redis,
                scorer=scorer,
                db_session_factory=async_session_factory,
            )
            logger.info("PersonaMonitor initialized", scorer=settings.persona_scorer)
        except Exception as e:
            logger.warning("PersonaMonitor initialization failed", error=str(e))

    # Compile graph with checkpointer and store
    app.state.graph = compile_graph(checkpointer, store=store)

    # Auto-seed product catalog if empty
    try:
        from app.catalog.auto_seed import auto_seed_catalog
        from app.core.database import async_session_factory

        async with async_session_factory() as session:
            await auto_seed_catalog(session)
    except Exception as e:
        logger.warning("Auto-seed failed (non-fatal)", error=str(e))

    yield

    if store_cm is not None:
        await store_cm.__aexit__(None, None, None)
    if checkpointer_cm is not None:
        await checkpointer_cm.__aexit__(None, None, None)

    logger.info("Shutting down Beauty Concierge API")


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Beauty Shopping Concierge",
        description="Multi-agent AI system for personalized beauty recommendations",
        version="1.0.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(chat.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(products.router, prefix="/api/v1")
    app.include_router(conversations.router, prefix="/api/v1")
    app.include_router(memory.router, prefix="/api/v1")
    app.include_router(persona.router, prefix="/api/v1")

    return app


app = create_app()
