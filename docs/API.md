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
  "product_count": 3
}
```

### POST /api/v1/chat/stream
SSE streaming chat endpoint.

**Request:** Same as POST /api/v1/chat

**Response:** Server-Sent Events
```
data: {"type": "token", "content": "Here"}
data: {"type": "token", "content": " are"}
data: {"type": "token", "content": " some"}
data: {"type": "done", "conversation_id": "uuid"}
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
Get product details.

## Conversations

### GET /api/v1/conversations?user_id=uuid
List conversations for a user.

### GET /api/v1/conversations/{conversation_id}/messages
Get messages for a conversation.

## Memory

### GET /api/v1/users/{user_id}/memory
Get all stored memories for a user.

### DELETE /api/v1/users/{user_id}/memory/{memory_id}
Delete a specific memory.

### GET /api/v1/users/{user_id}/memory/constraints
Get user's stored constraints.

### POST /api/v1/users/{user_id}/memory/constraints
Add a new constraint.

## Persona

### GET /api/v1/persona/scores?conversation_id=uuid&message_id=uuid
Get persona scores for a specific message.

### GET /api/v1/persona/history?conversation_id=uuid
Get persona score history for a conversation.

### GET /api/v1/persona/alerts?conversation_id=uuid
Get persona alerts (threshold violations).

### GET /api/v1/persona/stream?conversation_id=uuid
SSE stream for real-time persona updates.
