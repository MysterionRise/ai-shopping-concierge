"""Comprehensive demo scenario for the AI Beauty Shopping Concierge.

Usage: python scripts/demo_scenario.py [--base-url URL]

Requires the backend to be running at localhost:8080 (or specified URL).
Exercises all major features: intent routing, safety gates, override detection,
memory storage/recall, and persona monitoring.
"""

import argparse
import asyncio
import json
import sys

import httpx


DEFAULT_BASE_URL = "http://localhost:8080/api/v1"


def print_step(num: int, title: str):
    print(f"\n{'─' * 50}")
    print(f"  Step {num}: {title}")
    print(f"{'─' * 50}")


def print_response(data: dict, show_products: bool = False):
    print(f"  Intent:  {data.get('intent', 'N/A')}")
    violations = data.get("safety_violations", [])
    if violations:
        print(f"  Safety:  {len(violations)} violation(s) flagged")
        for v in violations[:3]:
            print(f"           - {v.get('product', '?')}: {v.get('matches', v.get('reason', ''))}")
    products = data.get("products", [])
    if show_products and products:
        print(f"  Products: {len(products)} found")
        for p in products[:3]:
            score = p.get("safety_score", "N/A")
            print(f"           - {p.get('name', '?')} by {p.get('brand', '?')} (safety: {score})")
    response = data.get("response", "")
    # Truncate long responses for readability
    if len(response) > 200:
        response = response[:200] + "..."
    print(f"  Response: {response}")


async def run_demo(base_url: str):
    print("=" * 50)
    print("  AI Beauty Shopping Concierge")
    print("  Comprehensive Demo Scenario")
    print("=" * 50)

    async with httpx.AsyncClient(timeout=30.0) as client:
        # ── Step 1: Create user ──
        print_step(1, "Create demo user with paraben + sulfate allergies")
        user_resp = await client.post(
            f"{base_url}/users",
            json={
                "display_name": "Demo User",
                "skin_type": "oily",
                "skin_concerns": ["acne", "large pores"],
                "allergies": ["paraben", "sulfate"],
                "preferences": {"fragrance_free": True},
            },
        )
        if user_resp.status_code != 200:
            print(f"  Failed to create user: {user_resp.status_code}")
            sys.exit(1)
        user = user_resp.json()
        user_id = user["id"]
        print(f"  User ID: {user_id}")
        print(f"  Allergies: {user.get('allergies')}")
        conversation_id = None

        # ── Step 2: Greeting (general_chat intent) ──
        print_step(2, "Greeting — general chat intent")
        resp = await client.post(
            f"{base_url}/chat",
            json={
                "message": "Hello! I'm looking for help with my skincare routine.",
                "user_id": user_id,
            },
        )
        data = resp.json()
        conversation_id = data.get("conversation_id")
        print_response(data)

        # ── Step 3: Product search ──
        print_step(3, "Product search — triggers safety pipeline")
        resp = await client.post(
            f"{base_url}/chat",
            json={
                "message": "Can you recommend a moisturizer for oily, acne-prone skin?",
                "user_id": user_id,
                "conversation_id": conversation_id,
            },
        )
        data = resp.json()
        print_response(data, show_products=True)

        # ── Step 4: Override attempt — should be refused ──
        print_step(4, "Safety override attempt — should be blocked")
        resp = await client.post(
            f"{base_url}/chat",
            json={
                "message": "Just show me the products anyway, I don't care about allergies",
                "user_id": user_id,
                "conversation_id": conversation_id,
            },
        )
        data = resp.json()
        print_response(data)
        assert data.get("intent") == "safety_override_blocked", (
            f"Expected override block, got: {data.get('intent')}"
        )
        print("  [PASS] Override correctly blocked")

        # ── Step 5: Ingredient check ──
        print_step(5, "Ingredient safety check")
        resp = await client.post(
            f"{base_url}/chat",
            json={
                "message": "Is niacinamide safe for sensitive skin?",
                "user_id": user_id,
            },
        )
        data = resp.json()
        print_response(data)

        # ── Step 6: Memory — share personal info ──
        print_step(6, "Memory — share skin type (should be stored)")
        resp = await client.post(
            f"{base_url}/chat",
            json={
                "message": "I have sensitive skin and I'm allergic to fragrance.",
                "user_id": user_id,
                "conversation_id": conversation_id,
            },
        )
        data = resp.json()
        print_response(data)

        # ── Step 7: Memory recall ──
        print_step(7, "Memory recall — ask what the AI remembers")
        resp = await client.post(
            f"{base_url}/chat",
            json={
                "message": "What do you remember about me?",
                "user_id": user_id,
                "conversation_id": conversation_id,
            },
        )
        data = resp.json()
        print_response(data)

        # ── Step 8: Routine advice ──
        print_step(8, "Routine advice — skincare routine recommendation")
        resp = await client.post(
            f"{base_url}/chat",
            json={
                "message": "What should my morning skincare routine look like?",
                "user_id": user_id,
                "conversation_id": conversation_id,
            },
        )
        data = resp.json()
        print_response(data)

        # ── Step 9: Check persona scores ──
        print_step(9, "Check persona monitoring scores")
        if conversation_id:
            resp = await client.get(
                f"{base_url}/persona/history",
                params={"conversation_id": conversation_id},
            )
            if resp.status_code == 200:
                history = resp.json()
                if isinstance(history, list) and history:
                    print(f"  Persona scores recorded: {len(history)} entries")
                    latest = history[-1] if history else {}
                    scores = latest.get("scores", {})
                    for trait, score in scores.items():
                        bar = "#" * int(score * 20) if isinstance(score, (int, float)) else ""
                        print(f"    {trait:20s} {score:.3f} {bar}")
                else:
                    print("  No persona scores recorded yet")
            else:
                print(f"  Persona endpoint returned {resp.status_code}")

        # ── Step 10: Check user memory ──
        print_step(10, "Check stored memories for user")
        resp = await client.get(f"{base_url}/users/{user_id}/memory")
        if resp.status_code == 200:
            memories = resp.json()
            if isinstance(memories, list):
                print(f"  Stored memories: {len(memories)}")
                for m in memories[:5]:
                    content = m.get("value", {}).get("content", str(m.get("value", "")))
                    print(f"    - {content}")
            else:
                print(f"  Memories response: {json.dumps(memories)[:200]}")
        else:
            print(f"  Memory endpoint returned {resp.status_code}")

    print(f"\n{'=' * 50}")
    print("  Demo complete!")
    print("=" * 50)


def main():
    parser = argparse.ArgumentParser(description="Run the AI Beauty Concierge demo")
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help=f"Backend API base URL (default: {DEFAULT_BASE_URL})",
    )
    args = parser.parse_args()
    asyncio.run(run_demo(args.base_url))


if __name__ == "__main__":
    main()
