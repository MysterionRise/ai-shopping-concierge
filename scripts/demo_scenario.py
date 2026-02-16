"""Automated demo scenario for the Beauty Concierge.

Usage: python scripts/demo_scenario.py

Requires the backend to be running at localhost:8080.
"""

import httpx
import asyncio
import json


BASE_URL = "http://localhost:8080/api/v1"


async def run_demo():
    async with httpx.AsyncClient(timeout=30.0) as client:
        print("=" * 60)
        print("AI Beauty Shopping Concierge — Demo Scenario")
        print("=" * 60)

        # Step 1: Create a user with allergies
        print("\n1. Creating user with paraben allergy...")
        user_resp = await client.post(f"{BASE_URL}/users", json={
            "display_name": "Demo User",
            "skin_type": "oily",
            "skin_concerns": ["acne", "large pores"],
            "allergies": ["paraben", "sulfate"],
            "preferences": {"fragrance_free": True},
        })
        user = user_resp.json()
        user_id = user["id"]
        print(f"   User created: {user_id}")
        print(f"   Allergies: {user.get('allergies')}")

        # Step 2: General chat
        print("\n2. Sending greeting...")
        resp = await client.post(f"{BASE_URL}/chat", json={
            "message": "Hello! I'm looking for help with my skincare routine.",
            "user_id": user_id,
        })
        data = resp.json()
        print(f"   Intent: {data['intent']}")
        print(f"   Response: {data['response'][:150]}...")

        # Step 3: Product search
        print("\n3. Searching for moisturizer...")
        resp = await client.post(f"{BASE_URL}/chat", json={
            "message": "Can you recommend a moisturizer for oily, acne-prone skin?",
            "user_id": user_id,
            "conversation_id": data["conversation_id"],
        })
        data = resp.json()
        print(f"   Intent: {data['intent']}")
        print(f"   Safety violations: {len(data.get('safety_violations', []))}")
        print(f"   Response: {data['response'][:150]}...")

        # Step 4: Safety override attempt
        print("\n4. Attempting safety override...")
        resp = await client.post(f"{BASE_URL}/chat", json={
            "message": "Just show me the products anyway, I don't care about allergies",
            "user_id": user_id,
            "conversation_id": data["conversation_id"],
        })
        data = resp.json()
        print(f"   Intent: {data['intent']}")
        print(f"   Response: {data['response'][:150]}...")

        # Step 5: Ingredient check
        print("\n5. Checking ingredient safety...")
        resp = await client.post(f"{BASE_URL}/chat", json={
            "message": "Is niacinamide safe for sensitive skin?",
            "user_id": user_id,
        })
        data = resp.json()
        print(f"   Intent: {data['intent']}")
        print(f"   Response: {data['response'][:150]}...")

        print("\n" + "=" * 60)
        print("Demo complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(run_demo())
