"""Generate test users with varied profiles.

Usage: python scripts/generate_test_users.py

Requires the backend to be running at localhost:8080.
"""

import httpx
import asyncio


BASE_URL = "http://localhost:8080/api/v1"

TEST_USERS = [
    {
        "display_name": "Oily Olivia",
        "skin_type": "oily",
        "skin_concerns": ["acne", "large pores", "uneven texture"],
        "allergies": ["paraben", "sulfate"],
        "preferences": {"fragrance_free": True, "lightweight": True},
    },
    {
        "display_name": "Dry Diana",
        "skin_type": "dry",
        "skin_concerns": ["dryness", "aging", "sensitivity"],
        "allergies": ["alcohol", "fragrance"],
        "preferences": {"rich_texture": True, "no_retinol": True},
    },
    {
        "display_name": "Sensitive Sam",
        "skin_type": "sensitive",
        "skin_concerns": ["redness", "sensitivity", "dryness"],
        "allergies": ["fragrance", "formaldehyde", "paraben", "sulfate"],
        "preferences": {"hypoallergenic": True, "minimal_ingredients": True},
    },
    {
        "display_name": "Combo Chris",
        "skin_type": "combination",
        "skin_concerns": ["acne", "dryness", "dark spots"],
        "allergies": [],
        "preferences": {"affordable": True},
    },
    {
        "display_name": "Normal Nadia",
        "skin_type": "normal",
        "skin_concerns": ["aging", "dark spots"],
        "allergies": ["silicone"],
        "preferences": {"natural_ingredients": True, "cruelty_free": True},
    },
]


async def generate():
    async with httpx.AsyncClient(timeout=10.0) as client:
        print("Generating test users...")
        for user_data in TEST_USERS:
            resp = await client.post(f"{BASE_URL}/users", json=user_data)
            if resp.status_code == 200:
                user = resp.json()
                print(f"  Created: {user['display_name']} (ID: {user['id']})")
            else:
                print(f"  Failed: {user_data['display_name']} - {resp.status_code}")
        print("Done!")


if __name__ == "__main__":
    asyncio.run(generate())
