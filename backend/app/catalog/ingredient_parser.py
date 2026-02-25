import re


def parse_ingredients(ingredients_text: str) -> list[str]:
    if not ingredients_text:
        return []

    # Split by comma, handling parenthetical content
    raw = re.split(r",(?![^(]*\))", ingredients_text)
    ingredients = []
    for item in raw:
        cleaned = item.strip().lower()
        # Remove INCI concentration indicators like [1-5%]
        cleaned = re.sub(r"\[.*?\]", "", cleaned)
        # Remove leading numbers/bullets
        cleaned = re.sub(r"^\d+[\.\)]\s*", "", cleaned)
        cleaned = cleaned.strip(" .")
        if cleaned and len(cleaned) > 1:
            ingredients.append(cleaned)
    return ingredients


def normalize_ingredient(name: str) -> str:
    return name.strip().lower()


KNOWN_ALLERGEN_SYNONYMS: dict[str, list[str]] = {
    "paraben": [
        "methylparaben",
        "ethylparaben",
        "propylparaben",
        "butylparaben",
        "isobutylparaben",
    ],
    "sulfate": [
        "sodium lauryl sulfate",
        "sodium laureth sulfate",
        "sls",
        "sles",
        "ammonium lauryl sulfate",
    ],
    "fragrance": [
        "parfum",
        "fragrance",
        "aroma",
        "linalool",
        "limonene",
        "citronellol",
        "geraniol",
        "eugenol",
        "coumarin",
    ],
    "alcohol": [
        "alcohol denat",
        "alcohol denat.",
        "sd alcohol",
        "isopropyl alcohol",
        "ethanol",
    ],
    "formaldehyde": [
        "formaldehyde",
        "dmdm hydantoin",
        "imidazolidinyl urea",
        "diazolidinyl urea",
        "quaternium-15",
    ],
    "silicone": [
        "dimethicone",
        "cyclomethicone",
        "cyclopentasiloxane",
        "amodimethicone",
        "trimethicone",
    ],
    "mineral oil": ["mineral oil", "paraffinum liquidum", "petrolatum", "petroleum"],
    "retinol": ["retinol", "retinyl palmitate", "retinaldehyde", "tretinoin", "adapalene"],
    "aha": ["glycolic acid", "lactic acid", "mandelic acid", "citric acid", "malic acid"],
    "bha": ["salicylic acid", "beta hydroxy acid", "willow bark extract"],
    "coconut": [
        "cocamidopropyl betaine",
        "sodium coco-sulfate",
        "caprylic/capric triglyceride",
        "coconut oil",
        "cocos nucifera oil",
    ],
    "propylene_glycol": ["propylene glycol", "propanediol", "1,2-propanediol"],
    "phenoxyethanol": ["phenoxyethanol", "2-phenoxyethanol"],
}

# Reverse index: maps each member ingredient to its group name for O(1) lookups.
# Also maps group names to themselves.
REVERSE_ALLERGEN_INDEX: dict[str, str] = {}
for _group, _members in KNOWN_ALLERGEN_SYNONYMS.items():
    REVERSE_ALLERGEN_INDEX[_group] = _group
    for _member in _members:
        REVERSE_ALLERGEN_INDEX[_member] = _group


def get_allergen_group(ingredient: str) -> str | None:
    normalized = normalize_ingredient(ingredient)
    return REVERSE_ALLERGEN_INDEX.get(normalized)


def find_allergen_matches(ingredients: list[str], allergens: list[str]) -> list[dict[str, str]]:
    matches = []
    allergen_groups = set()

    for allergen in allergens:
        normalized_allergen = normalize_ingredient(allergen)
        # Check if allergen is a group name
        if normalized_allergen in KNOWN_ALLERGEN_SYNONYMS:
            allergen_groups.add(normalized_allergen)
        else:
            # Check if it belongs to a group
            group = get_allergen_group(normalized_allergen)
            if group:
                allergen_groups.add(group)
            else:
                allergen_groups.add(normalized_allergen)

    for ingredient in ingredients:
        normalized = normalize_ingredient(ingredient)
        # Direct match
        for allergen in allergens:
            if normalize_ingredient(allergen) == normalized:
                matches.append(
                    {"ingredient": ingredient, "allergen": allergen, "match_type": "direct"}
                )
                break
        else:
            # Group match
            group = get_allergen_group(normalized)
            if group and group in allergen_groups:
                matches.append({"ingredient": ingredient, "allergen": group, "match_type": "group"})

    return matches
