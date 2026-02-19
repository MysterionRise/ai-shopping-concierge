"""Tests for persona vector loading and mock vector generation."""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.persona.traits import PERSONA_TRAITS, get_trait_by_name


class TestTraitDefinitions:
    def test_all_traits_have_contrast_pairs(self):
        for trait in PERSONA_TRAITS:
            assert len(trait.contrast_pairs) >= 10, (
                f"Trait '{trait.name}' has only {len(trait.contrast_pairs)} "
                f"contrast pairs, expected >= 10"
            )

    def test_trait_count(self):
        assert len(PERSONA_TRAITS) == 5

    def test_trait_names(self):
        names = {t.name for t in PERSONA_TRAITS}
        assert names == {
            "sycophancy",
            "hallucination",
            "over_confidence",
            "safety_bypass",
            "sales_pressure",
        }

    def test_get_trait_by_name(self):
        trait = get_trait_by_name("sycophancy")
        assert trait is not None
        assert trait.name == "sycophancy"
        assert trait.threshold == 0.65

    def test_get_trait_by_name_not_found(self):
        assert get_trait_by_name("nonexistent") is None

    def test_trait_thresholds(self):
        for trait in PERSONA_TRAITS:
            assert (
                0.0 < trait.threshold < 1.0
            ), f"Trait '{trait.name}' has invalid threshold: {trait.threshold}"

    def test_contrast_pairs_are_tuples(self):
        for trait in PERSONA_TRAITS:
            for i, pair in enumerate(trait.contrast_pairs):
                assert (
                    isinstance(pair, tuple) and len(pair) == 2
                ), f"Trait '{trait.name}' pair {i} is not a 2-tuple"
                assert isinstance(pair[0], str) and isinstance(
                    pair[1], str
                ), f"Trait '{trait.name}' pair {i} contains non-string values"

    def test_trait_has_primary_prompts(self):
        for trait in PERSONA_TRAITS:
            assert trait.positive_prompt, f"Trait '{trait.name}' missing positive_prompt"
            assert trait.negative_prompt, f"Trait '{trait.name}' missing negative_prompt"

    def test_safety_bypass_lowest_threshold(self):
        safety = get_trait_by_name("safety_bypass")
        assert safety is not None
        for trait in PERSONA_TRAITS:
            if trait.name != "safety_bypass":
                assert safety.threshold <= trait.threshold


class TestMockVectors:
    def test_generate_mock_vectors(self):
        torch = pytest.importorskip("torch")
        from app.persona.vector_extractor import HIDDEN_DIM, generate_mock_vectors

        with tempfile.TemporaryDirectory() as tmpdir:
            output_dir = Path(tmpdir)
            generate_mock_vectors(output_dir)

            # Check all trait vectors were created
            for trait in PERSONA_TRAITS:
                pt_file = output_dir / f"{trait.name}.pt"
                assert pt_file.exists(), f"Missing vector for {trait.name}"

                vector = torch.load(pt_file, weights_only=True)
                assert vector.shape == (
                    HIDDEN_DIM,
                ), f"Wrong shape for {trait.name}: {vector.shape}"
                # Check approximately unit norm
                assert abs(vector.norm().item() - 1.0) < 0.01

    def test_generate_mock_vectors_deterministic(self):
        torch = pytest.importorskip("torch")
        from app.persona.vector_extractor import generate_mock_vectors

        with tempfile.TemporaryDirectory() as d1, tempfile.TemporaryDirectory() as d2:
            generate_mock_vectors(Path(d1))
            generate_mock_vectors(Path(d2))

            for trait in PERSONA_TRAITS:
                v1 = torch.load(Path(d1) / f"{trait.name}.pt", weights_only=True)
                v2 = torch.load(Path(d2) / f"{trait.name}.pt", weights_only=True)
                assert torch.equal(v1, v2), f"Non-deterministic vector for {trait.name}"


class TestLoadVectors:
    def test_load_real_vectors_first(self):
        torch = pytest.importorskip("torch")
        from app.persona.vector_extractor import HIDDEN_DIM, PersonaVectorExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            real_dir = Path(tmpdir) / "vectors"
            real_dir.mkdir()
            mock_dir = real_dir / "mock"
            mock_dir.mkdir()

            # Create a real vector
            real_vec = torch.randn(HIDDEN_DIM)
            torch.save(real_vec, real_dir / "sycophancy.pt")

            # Create a mock vector (different)
            mock_vec = torch.ones(HIDDEN_DIM)
            torch.save(mock_vec, mock_dir / "sycophancy.pt")

            with patch.object(
                PersonaVectorExtractor,
                "load_vectors",
                wraps=PersonaVectorExtractor.load_vectors,
            ):
                # load_vectors should prefer real vectors
                vectors = PersonaVectorExtractor.load_vectors(real_dir)
                assert "sycophancy" in vectors
                assert torch.equal(vectors["sycophancy"], real_vec)

    def test_fallback_to_mock_vectors(self):
        torch = pytest.importorskip("torch")
        from app.persona.vector_extractor import HIDDEN_DIM, PersonaVectorExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            vectors_dir = Path(tmpdir) / "vectors"
            vectors_dir.mkdir()
            mock_dir = vectors_dir / "mock"
            mock_dir.mkdir()

            # Only create mock vectors (no real ones)
            mock_vec = torch.ones(HIDDEN_DIM)
            torch.save(mock_vec, mock_dir / "sycophancy.pt")

            vectors = PersonaVectorExtractor.load_vectors(vectors_dir)
            assert "sycophancy" in vectors
            assert torch.equal(vectors["sycophancy"], mock_vec)

    def test_empty_directories_returns_empty(self):
        pytest.importorskip("torch")
        from app.persona.vector_extractor import PersonaVectorExtractor

        with tempfile.TemporaryDirectory() as tmpdir:
            empty_dir = Path(tmpdir) / "vectors"
            empty_dir.mkdir()

            vectors = PersonaVectorExtractor.load_vectors(empty_dir)
            assert vectors == {}
