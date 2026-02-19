"""Ingredient-to-ingredient interaction database.

Flags known incompatible ingredient combinations within a single product.
Based on dermatological consensus about actives that should not be mixed.
"""

from app.catalog.ingredient_parser import normalize_ingredient

# Each interaction maps a pair of ingredient groups to a description.
# The pair is sorted alphabetically so lookup is deterministic.
INTERACTION_DB: list[dict] = [
    {
        "group_a": ["retinol", "retinyl palmitate", "retinaldehyde", "tretinoin", "adapalene"],
        "group_b": ["glycolic acid", "lactic acid", "mandelic acid", "malic acid"],
        "severity": "high",
        "concern": (
            "Retinoids + AHAs together can cause excessive irritation, peeling, "
            "and compromised skin barrier. Use on alternate days instead."
        ),
        "label": "Retinoid + AHA",
    },
    {
        "group_a": ["retinol", "retinyl palmitate", "retinaldehyde", "tretinoin", "adapalene"],
        "group_b": ["salicylic acid"],
        "severity": "high",
        "concern": (
            "Retinoids + BHA (salicylic acid) together increase irritation risk "
            "and skin sensitivity. Best used at different times of day."
        ),
        "label": "Retinoid + BHA",
    },
    {
        "group_a": ["retinol", "retinyl palmitate", "retinaldehyde", "tretinoin", "adapalene"],
        "group_b": ["benzoyl peroxide"],
        "severity": "high",
        "concern": (
            "Benzoyl peroxide can oxidize and deactivate retinol, "
            "reducing effectiveness of both. Apply at different times."
        ),
        "label": "Retinoid + Benzoyl Peroxide",
    },
    {
        "group_a": ["ascorbic acid", "l-ascorbic acid", "vitamin c"],
        "group_b": ["niacinamide"],
        "severity": "low",
        "concern": (
            "Vitamin C + niacinamide was historically thought to cause flushing, "
            "but modern formulations are generally safe together. "
            "Some sensitive skin types may experience mild irritation."
        ),
        "label": "Vitamin C + Niacinamide",
    },
    {
        "group_a": ["ascorbic acid", "l-ascorbic acid", "vitamin c"],
        "group_b": ["retinol", "retinyl palmitate", "retinaldehyde", "tretinoin", "adapalene"],
        "severity": "medium",
        "concern": (
            "Vitamin C and retinoids both work best at different pH levels. "
            "Using together may reduce efficacy. Apply vitamin C in the morning "
            "and retinoid at night."
        ),
        "label": "Vitamin C + Retinoid",
    },
    {
        "group_a": ["glycolic acid", "lactic acid", "mandelic acid"],
        "group_b": ["salicylic acid"],
        "severity": "medium",
        "concern": (
            "AHA + BHA together can over-exfoliate, leading to dryness, "
            "redness, and barrier damage. Use on alternate days."
        ),
        "label": "AHA + BHA",
    },
    {
        "group_a": ["benzoyl peroxide"],
        "group_b": ["ascorbic acid", "l-ascorbic acid", "vitamin c"],
        "severity": "high",
        "concern": (
            "Benzoyl peroxide oxidizes vitamin C, rendering both less effective. "
            "Apply at different times of day."
        ),
        "label": "Benzoyl Peroxide + Vitamin C",
    },
    {
        "group_a": ["hydroquinone"],
        "group_b": ["benzoyl peroxide"],
        "severity": "medium",
        "concern": (
            "Benzoyl peroxide can temporarily stain skin dark when combined "
            "with hydroquinone. Apply at different times."
        ),
        "label": "Hydroquinone + Benzoyl Peroxide",
    },
    {
        "group_a": ["glycolic acid", "lactic acid", "mandelic acid", "salicylic acid"],
        "group_b": ["ascorbic acid", "l-ascorbic acid", "vitamin c"],
        "severity": "medium",
        "concern": (
            "Using exfoliating acids with vitamin C can increase sensitivity "
            "and reduce vitamin C stability. Layer carefully or use at different times."
        ),
        "label": "Exfoliating Acid + Vitamin C",
    },
    {
        "group_a": ["niacinamide"],
        "group_b": ["glycolic acid", "lactic acid", "mandelic acid", "salicylic acid"],
        "severity": "low",
        "concern": (
            "Niacinamide + direct acids at low pH may cause temporary flushing. "
            "Wait a few minutes between applications or use at different times."
        ),
        "label": "Niacinamide + Direct Acid",
    },
]


def find_ingredient_interactions(ingredients: list[str]) -> list[dict]:
    """Check a product's ingredient list for known interactions.

    Returns a list of interaction warnings, each with:
    - ingredient_a: the first ingredient found
    - ingredient_b: the second ingredient found
    - severity: high / medium / low
    - concern: human-readable explanation
    - label: short label for the interaction
    """
    normalized = {normalize_ingredient(i): i for i in ingredients}
    norm_set = set(normalized.keys())

    warnings: list[dict] = []
    seen_labels: set[str] = set()

    for interaction in INTERACTION_DB:
        # Find matches in group_a and group_b
        match_a = None
        match_b = None
        for member in interaction["group_a"]:
            if member in norm_set:
                match_a = normalized[member]
                break
        if match_a is None:
            continue
        for member in interaction["group_b"]:
            if member in norm_set:
                match_b = normalized[member]
                break
        if match_b is None:
            continue

        # Avoid duplicate labels (same interaction matched via different members)
        label = interaction["label"]
        if label in seen_labels:
            continue
        seen_labels.add(label)

        warnings.append(
            {
                "ingredient_a": match_a,
                "ingredient_b": match_b,
                "severity": interaction["severity"],
                "concern": interaction["concern"],
                "label": label,
            }
        )

    return warnings
