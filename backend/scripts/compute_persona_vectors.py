"""Compute persona vectors from trait contrast pairs.

Usage:
    cd backend && python -m scripts.compute_persona_vectors [--device cpu|cuda] [--mock]

Requires: pip install -e ".[persona]"  (torch, transformers, accelerate)
The --mock flag generates random vectors for dev/CI without requiring ML dependencies.
"""

import argparse
import sys

import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.dev.ConsoleRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

logger = structlog.get_logger()


def compute_real_vectors(device: str) -> None:
    """Compute real persona vectors using Llama 3.1 8B."""
    try:
        import torch
    except ImportError:
        logger.error("torch not installed. Run: pip install -e '.[persona]'")
        sys.exit(1)

    from app.persona.traits import PERSONA_TRAITS
    from app.persona.vector_extractor import PersonaVectorExtractor

    if device == "cuda" and not torch.cuda.is_available():
        logger.warning("CUDA not available, falling back to CPU")
        device = "cpu"

    logger.info("Computing vectors", device=device, trait_count=len(PERSONA_TRAITS))

    extractor = PersonaVectorExtractor()
    extractor.compute_all_vectors()

    # Print vector statistics
    logger.info("=== Vector Statistics ===")
    for name, vector in extractor.persona_vectors.items():
        logger.info(
            "Vector computed",
            trait=name,
            norm=round(vector.norm().item(), 4),
            shape=tuple(vector.shape),
        )

    # Print inter-trait cosine distances
    names = list(extractor.persona_vectors.keys())
    vectors = list(extractor.persona_vectors.values())

    if len(vectors) > 1:
        logger.info("=== Inter-Trait Cosine Distances ===")
        for i in range(len(names)):
            for j in range(i + 1, len(names)):
                sim = torch.nn.functional.cosine_similarity(
                    vectors[i].unsqueeze(0), vectors[j].unsqueeze(0)
                )
                logger.info(
                    "Cosine similarity",
                    pair=f"{names[i]} <-> {names[j]}",
                    similarity=round(sim.item(), 4),
                )

    logger.info("Done! Vectors saved to backend/app/persona/vectors/")


def compute_mock_vectors() -> None:
    """Generate random mock vectors for dev/CI."""
    from app.persona.vector_extractor import generate_mock_vectors

    generate_mock_vectors()
    logger.info("Mock vectors generated successfully")


def main():
    parser = argparse.ArgumentParser(description="Compute persona trait vectors")
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device for model inference (default: cpu)",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Generate random mock vectors (no ML dependencies required)",
    )
    args = parser.parse_args()

    if args.mock:
        compute_mock_vectors()
    else:
        compute_real_vectors(args.device)


if __name__ == "__main__":
    main()
