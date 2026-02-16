# Persona Vector Monitoring

## Overview

This system implements activation-based persona monitoring inspired by [Anthropic's research on representation engineering](https://www.anthropic.com/research). By analyzing the hidden state activations of a language model, we can detect when the model exhibits undesirable behavioral traits.

## How It Works

### 1. Contrast Pair Definition

For each behavioral trait we want to monitor, we define a contrast pair:
- **Positive prompt:** Describes the undesirable behavior (e.g., sycophancy)
- **Negative prompt:** Describes the desired behavior (e.g., honest advice)

### 2. Persona Vector Extraction

For each contrast pair:
1. Run the positive prompt through Llama 3.1 8B and collect hidden state activations at layer 16
2. Run the negative prompt through the same model
3. Compute the mean difference: `vector = mean(pos_activations) - mean(neg_activations)`

This vector represents the "direction" of the undesirable trait in the model's representation space.

### 3. Response Scoring

For each AI response:
1. Run the full conversation (prompt + response) through the model
2. Extract activations at the same layer
3. Compute cosine similarity between the response activations and each persona vector
4. Normalize to 0-1 range

A high score means the response's internal representations are closer to the undesirable behavior direction.

## Monitored Traits

| Trait | Threshold | What It Detects |
|-------|-----------|-----------------|
| Sycophancy | 0.65 | Agreeing with the user instead of being honest |
| Hallucination | 0.70 | Making unverified claims about products |
| Over-confidence | 0.70 | Making strong guarantees about results |
| Safety Bypass | 0.60 | Willingness to override safety constraints |
| Sales Pressure | 0.70 | Pushy upselling behavior |

## Hardware Requirements

- **CPU inference:** ~16GB RAM, 5-10 seconds per evaluation
- **GPU inference:** ~6GB VRAM, <1 second per evaluation
- Model download: ~16GB (one-time)

## Pre-computing Vectors

```bash
cd backend
pip install -e ".[persona]"
python -m scripts.compute_persona_vectors
```

This saves `.pt` files to `backend/app/persona/vectors/`.

## Configuration

Set `PERSONA_ENABLED=true` in `.env` to enable monitoring. When disabled, no model is loaded and no scoring occurs.
