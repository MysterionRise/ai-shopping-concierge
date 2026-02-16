"""Persona vector extraction using raw transformers + PyTorch.

Loads Llama 3.1 8B directly for hidden state activation access.
NOT through Ollama — we need intermediate layer hidden states.

Hardware: ~16GB RAM for CPU inference or ~6GB VRAM for GPU.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import structlog

from app.persona.traits import PERSONA_TRAITS, TraitDefinition

if TYPE_CHECKING:
    import torch

logger = structlog.get_logger()

VECTORS_DIR = Path(__file__).parent / "vectors"
MODEL_NAME = "meta-llama/Llama-3.1-8B-Instruct"
TARGET_LAYER = 16  # Middle layer for activation extraction


class PersonaVectorExtractor:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.persona_vectors = {}
        self._loaded = False

    def _load_model(self):
        if self._loaded:
            return

        try:
            import torch
            from transformers import AutoModelForCausalLM, AutoTokenizer

            logger.info("Loading model for persona extraction", model=MODEL_NAME)
            self.tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
            self.model = AutoModelForCausalLM.from_pretrained(
                MODEL_NAME,
                torch_dtype=torch.float16,
                device_map="auto",
                output_hidden_states=True,
            )
            self._loaded = True
            logger.info("Model loaded successfully")
        except ImportError:
            logger.warning("torch/transformers not installed — persona monitoring disabled")
        except Exception as e:
            logger.error("Failed to load model", error=str(e))

    def extract_vector(self, trait_def: TraitDefinition) -> torch.Tensor | None:
        self._load_model()
        if not self.model:
            return None

        # Generate activations for positive (undesirable) prompt
        pos_acts = self._get_activations(trait_def.positive_prompt)
        # Generate activations for negative (desired) prompt
        neg_acts = self._get_activations(trait_def.negative_prompt)

        if pos_acts is None or neg_acts is None:
            return None

        # Persona vector = mean difference
        vector = pos_acts.mean(dim=1) - neg_acts.mean(dim=1)
        return vector.squeeze()

    def _get_activations(self, prompt: str) -> torch.Tensor | None:
        import torch

        if not self.model or not self.tokenizer:
            return None

        inputs = self.tokenizer(prompt, return_tensors="pt").to(self.model.device)
        with torch.no_grad():
            outputs = self.model(**inputs)

        hidden_states = outputs.hidden_states
        if TARGET_LAYER < len(hidden_states):
            return hidden_states[TARGET_LAYER].cpu()
        return hidden_states[-1].cpu()

    def score_response(
        self,
        prompt: str,
        response: str,
        persona_vectors: dict[str, torch.Tensor] | None = None,
    ) -> dict[str, float]:
        import torch

        self._load_model()
        if not self.model:
            return {t.name: 0.0 for t in PERSONA_TRAITS}

        vectors = persona_vectors or self.persona_vectors
        if not vectors:
            self.load_precomputed_vectors()
            vectors = self.persona_vectors

        full_text = f"User: {prompt}\nAssistant: {response}"
        activations = self._get_activations(full_text)
        if activations is None:
            return {t.name: 0.0 for t in PERSONA_TRAITS}

        mean_act = activations.mean(dim=1).squeeze()
        scores = {}
        for trait_name, vector in vectors.items():
            # Cosine similarity between response activations and persona vector
            similarity = torch.nn.functional.cosine_similarity(
                mean_act.unsqueeze(0), vector.unsqueeze(0)
            )
            # Normalize to 0-1 range
            score = (similarity.item() + 1) / 2
            scores[trait_name] = round(score, 4)

        return scores

    def save_vectors(self):
        import torch

        VECTORS_DIR.mkdir(parents=True, exist_ok=True)
        for name, vector in self.persona_vectors.items():
            path = VECTORS_DIR / f"{name}.pt"
            torch.save(vector, path)
            logger.info("Saved persona vector", trait=name, path=str(path))

    def load_precomputed_vectors(self):
        import torch

        if not VECTORS_DIR.exists():
            logger.warning("No precomputed vectors found")
            return

        for pt_file in VECTORS_DIR.glob("*.pt"):
            name = pt_file.stem
            self.persona_vectors[name] = torch.load(pt_file, weights_only=True)
            logger.info("Loaded persona vector", trait=name)

    def compute_all_vectors(self):
        for trait in PERSONA_TRAITS:
            logger.info("Computing vector", trait=trait.name)
            vector = self.extract_vector(trait)
            if vector is not None:
                self.persona_vectors[trait.name] = vector
        self.save_vectors()
