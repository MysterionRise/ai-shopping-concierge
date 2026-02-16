"""One-time script to pre-compute persona vectors for all 5 traits.

Usage: cd backend && python -m scripts.compute_persona_vectors

Requires: torch, transformers, accelerate (~16GB RAM or 6GB VRAM)
"""

import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


def main():
    try:
        from app.persona.vector_extractor import PersonaVectorExtractor
    except ImportError:
        logger.error(
            "torch/transformers not installed. "
            "Install with: pip install -e '.[persona]'"
        )
        return

    extractor = PersonaVectorExtractor()
    logger.info("Computing persona vectors for all traits...")
    extractor.compute_all_vectors()
    logger.info("Done! Vectors saved to backend/app/persona/vectors/")


if __name__ == "__main__":
    main()
