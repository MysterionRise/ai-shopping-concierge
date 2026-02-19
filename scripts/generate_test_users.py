"""Generate test users with varied profiles for demo and testing.

Usage: python scripts/generate_test_users.py

Requires the backend to be running at localhost:8080.

Creates 5 diverse demo personas covering different skin types, concerns,
allergy profiles, and preference patterns. Each persona is designed to
exercise different parts of the safety pipeline.
"""

import asyncio

import httpx


BASE_URL = "http://localhost:8080/api/v1"

TEST_USERS = [
    {
        "display_name": "Oily Olivia",
        "skin_type": "oily",
        "skin_concerns": ["acne", "large pores", "uneven texture"],
        "allergies": ["paraben", "sulfate"],
        "preferences": {
            "fragrance_free": True,
            "lightweight": True,
            "budget": "mid-range",
        },
    },
    {
        "display_name": "Dry Diana",
        "skin_type": "dry",
        "skin_concerns": ["dryness", "aging", "sensitivity"],
        "allergies": ["alcohol", "fragrance"],
        "preferences": {
            "rich_texture": True,
            "no_retinol": True,
            "budget": "premium",
        },
    },
    {
        "display_name": "Sensitive Sam",
        "skin_type": "sensitive",
        "skin_concerns": ["redness", "sensitivity", "dryness"],
        "allergies": ["fragrance", "formaldehyde", "paraben", "sulfate"],
        "preferences": {
            "hypoallergenic": True,
            "minimal_ingredients": True,
            "budget": "any",
        },
    },
    {
        "display_name": "Combo Chris",
        "skin_type": "combination",
        "skin_concerns": ["acne", "dryness", "dark spots"],
        "allergies": [],
        "preferences": {
            "affordable": True,
            "budget": "drugstore",
        },
    },
    {
        "display_name": "Normal Nadia",
        "skin_type": "normal",
        "skin_concerns": ["aging", "dark spots"],
        "allergies": ["silicone"],
        "preferences": {
            "natural_ingredients": True,
            "cruelty_free": True,
            "budget": "premium",
        },
    },
]


async def generate():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("=" * 50)
        print("Generating Demo Users")
        print("=" * 50)
        created_users = []
        for user_data in TEST_USERS:
            resp = await client.post(f"{BASE_URL}/users", json=user_data)
            if resp.status_code == 200:
                user = resp.json()
                created_users.append(user)
                allergies = user.get("allergies", [])
                allergy_str = ", ".join(allergies) if allergies else "none"
                print(
                    f"  + {user['display_name']} "
                    f"({user['skin_type']} skin, allergies: {allergy_str})"
                )
                print(f"    ID: {user['id']}")
            else:
                print(f"  x {user_data['display_name']} — HTTP {resp.status_code}")

        print(f"\nCreated {len(created_users)}/{len(TEST_USERS)} users")
        if created_users:
            print(f"\nUse any user ID with: POST /api/v1/chat")
            print(f'  {{"user_id": "{created_users[0]["id"]}", "message": "Hello!"}}')
        print("=" * 50)


if __name__ == "__main__":
    asyncio.run(generate())
