# API Reference

Base URL: `http://localhost:8080`

## Health

### GET /health
Check service health.

**Response 200:**
```json
{
  "status": "healthy",
  "postgres": "ok",
  "redis": "ok"
}
```

## Chat

### POST /api/v1/chat
Send a chat message and receive a response.

**Request:**
```json
{
  "message": "I need a moisturizer for oily skin",
  "user_id": "uuid-here",
  "conversation_id": "optional-uuid"
}
```

**Response:**
```json
{
  "response": "Here are some great options for oily skin...",
  "conversation_id": "uuid",
  "intent": "product_search",
  "safety_violations": [],
  "product_count": 3,
  "products": [
    {
      "id": "uuid",
      "name": "Product Name",
      "brand": "Brand",
      "safety_score": 8.5,
      "key_ingredients": ["niacinamide", "hyaluronic acid"],
      "ingredient_interactions": [],
      "fit_reasons": ["Matches your search for moisturizer"]
    }
  ]
}
```

**Override detection:** If the message contains override language (e.g., "show it anyway", "ignore my allergies"), the response will have `intent: "safety_override_blocked"` and a refusal message.

### POST /api/v1/chat/stream
SSE streaming chat endpoint.

**Request:** Same as POST /api/v1/chat

**Response:** Server-Sent Events
```
data: {"type": "token", "content": "Here"}
data: {"type": "token", "content": " are"}
data: {"type": "token", "content": " some"}
data: {"type": "products", "products": [...]}
data: {"type": "done", "conversation_id": "uuid"}
```

**Error events:**
```
data: {"type": "error", "content": "Response timed out. Please try again."}
```

## Users

### POST /api/v1/users
Create a new user.

**Request:**
```json
{
  "display_name": "Jane Doe",
  "skin_type": "oily",
  "skin_concerns": ["acne", "large pores"],
  "allergies": ["paraben", "sulfate"],
  "preferences": {"fragrance_free": true}
}
```

### GET /api/v1/users/{user_id}
Get user profile.

### PATCH /api/v1/users/{user_id}
Update user profile. All fields optional.

## Products

### GET /api/v1/products/search?q=moisturizer&limit=10
Search products by name, brand, or ingredients.

### GET /api/v1/products/{product_id}
Get product details including ingredients, safety score, and ingredient interactions.

## Conversations

### GET /api/v1/conversations?user_id=uuid
List conversations for a user.

### GET /api/v1/conversations/{conversation_id}/messages
Get messages for a conversation.

## Memory

### GET /api/v1/users/{user_id}/memory
Get all stored memories for a user (facts and constraints from LangMem store).

### DELETE /api/v1/users/{user_id}/memory/{memory_id}
Delete a specific memory.

### GET /api/v1/users/{user_id}/memory/constraints
Get user's stored constraints (allergies and sensitivities).

### POST /api/v1/users/{user_id}/memory/constraints
Add a new constraint.

**Request:**
```json
{
  "ingredient": "paraben",
  "severity": "absolute",
  "source": "user_stated"
}
```

## Persona Monitoring

### GET /api/v1/persona/scores?conversation_id=uuid&message_id=uuid
Get persona scores for a specific message.

**Response:**
```json
{
  "conversation_id": "uuid",
  "message_id": "uuid",
  "scores": {
    "sycophancy": 0.12,
    "hallucination": 0.08,
    "over_confidence": 0.15,
    "safety_bypass": 0.05,
    "sales_pressure": 0.10
  },
  "timestamp": "2025-01-01T12:00:00Z"
}
```

### GET /api/v1/persona/history?conversation_id=uuid
Get persona score history for a conversation. Returns all scores ordered by timestamp.

### GET /api/v1/persona/alerts?conversation_id=uuid
Get persona alerts (threshold violations) for a conversation.

### GET /api/v1/persona/stream?conversation_id=uuid
SSE stream for real-time persona updates.

**Events:**
```
data: {"scores": {...}, "conversation_id": "uuid", "message_id": "uuid", "timestamp": "..."}
data: {"type": "intervention", "intervention_type": "disclaimer", "trait": "hallucination", "text": "...", "message_id": "uuid"}
```
