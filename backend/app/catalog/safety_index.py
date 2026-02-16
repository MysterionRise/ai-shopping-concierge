from app.catalog.ingredient_parser import normalize_ingredient

# Risk levels: high (serious concern), medium (moderate concern), low (mild concern)
IRRITANT_DB: dict[str, dict] = {
    "sodium lauryl sulfate": {"risk": "high", "concern": "skin irritant, disrupts skin barrier"},
    "sodium laureth sulfate": {"risk": "medium", "concern": "potential irritant, drying"},
    "alcohol denat": {"risk": "medium", "concern": "drying, can irritate sensitive skin"},
    "alcohol denat.": {"risk": "medium", "concern": "drying, can irritate sensitive skin"},
    "fragrance": {"risk": "medium", "concern": "common allergen, undisclosed chemicals"},
    "parfum": {"risk": "medium", "concern": "common allergen, undisclosed chemicals"},
    "formaldehyde": {"risk": "high", "concern": "known carcinogen"},
    "dmdm hydantoin": {"risk": "high", "concern": "formaldehyde releaser"},
    "methylisothiazolinone": {"risk": "high", "concern": "strong sensitizer"},
    "methylchloroisothiazolinone": {"risk": "high", "concern": "strong sensitizer"},
    "triclosan": {"risk": "high", "concern": "endocrine disruptor"},
    "toluene": {"risk": "high", "concern": "toxic, reproductive concerns"},
    "hydroquinone": {"risk": "high", "concern": "potential carcinogen, skin irritant"},
    "oxybenzone": {"risk": "medium", "concern": "endocrine disruptor, photoallergic"},
    "octinoxate": {"risk": "medium", "concern": "endocrine disruptor"},
}

COMEDOGENIC_DB: dict[str, int] = {
    "coconut oil": 4,
    "cocoa butter": 4,
    "wheat germ oil": 5,
    "isopropyl myristate": 5,
    "isopropyl palmitate": 4,
    "lanolin": 4,
    "acetylated lanolin": 4,
    "soybean oil": 3,
    "corn oil": 3,
    "myristyl myristate": 5,
    "oleic acid": 3,
    "lauric acid": 4,
}


def compute_safety_score(ingredients: list[str]) -> tuple[float, list[dict]]:
    if not ingredients:
        return 5.0, []

    score = 10.0
    flags: list[dict] = []

    for ingredient in ingredients:
        normalized = normalize_ingredient(ingredient)

        if normalized in IRRITANT_DB:
            info = IRRITANT_DB[normalized]
            penalty = {"high": 2.0, "medium": 1.0, "low": 0.5}.get(info["risk"], 0.5)
            score -= penalty
            flags.append(
                {
                    "ingredient": ingredient,
                    "type": "irritant",
                    "risk": info["risk"],
                    "concern": info["concern"],
                }
            )

        if normalized in COMEDOGENIC_DB:
            rating = COMEDOGENIC_DB[normalized]
            if rating >= 4:
                score -= 1.5
                flags.append(
                    {
                        "ingredient": ingredient,
                        "type": "comedogenic",
                        "rating": rating,
                        "concern": f"comedogenic rating {rating}/5",
                    }
                )
            elif rating >= 3:
                score -= 0.5
                flags.append(
                    {
                        "ingredient": ingredient,
                        "type": "comedogenic",
                        "rating": rating,
                        "concern": f"comedogenic rating {rating}/5",
                    }
                )

    return max(0.0, min(10.0, round(score, 1))), flags
