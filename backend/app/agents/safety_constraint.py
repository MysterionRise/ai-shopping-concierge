import re

import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.catalog.ingredient_parser import (
    KNOWN_ALLERGEN_SYNONYMS,
    find_allergen_matches,
    normalize_ingredient,
    parse_ingredients,
)
from app.core.llm import get_llm

logger = structlog.get_logger()

SAFETY_LLM_PROMPT = """You are a safety checker for beauty products.
Given the user's known allergies/sensitivities and a list of products with their ingredients,
identify any products that may be unsafe.

User allergies: {allergies}

Products:
{products}

For each product, respond with:
- SAFE if no concerns
- UNSAFE: <reason> if there are concerns

Be thorough — check for ingredient synonyms and related compounds.
For example, "paraben allergy" means ALL parabens (methylparaben, ethylparaben, etc.) are unsafe."""

OVERRIDE_REFUSAL = (
    "I understand you'd like to see those products, but I can't recommend items "
    "containing ingredients you're allergic to. Your safety is my top priority. "
    "I can help you find alternatives that work for your skin without those ingredients."
)


def expand_allergens(allergens: list[str]) -> list[str]:
    """Expand allergen names into a full list including all known synonyms.

    For example, ["paraben"] expands to
    ["paraben", "methylparaben", "ethylparaben", "propylparaben", ...].
    """
    expanded: set[str] = set()
    for allergen in allergens:
        normalized = normalize_ingredient(allergen)
        expanded.add(normalized)
        # If it's a group name, add all members
        if normalized in KNOWN_ALLERGEN_SYNONYMS:
            expanded.update(KNOWN_ALLERGEN_SYNONYMS[normalized])
        else:
            # Check if it belongs to a group — add the group + all members
            for group, members in KNOWN_ALLERGEN_SYNONYMS.items():
                if normalized in members:
                    expanded.add(group)
                    expanded.update(members)
                    break
    return sorted(expanded)


async def safety_pre_filter_node(state: AgentState) -> dict:
    """Pre-filter node that prepares allergen data before product discovery.

    Runs after triage_router, before product_discovery.  Expands the user's
    hard_constraints (allergens) into a full synonym list so that
    product_discovery can filter at the search level.

    Only performs expansion for product_search and ingredient_check intents;
    for other intents the state passes through unchanged.
    """
    intent = state.get("current_intent", "general_chat")
    hard_constraints = state.get("hard_constraints", [])

    if intent not in ("product_search", "ingredient_check"):
        logger.info(
            "Safety pre-filter skipped (intent not product-related)",
            intent=intent,
        )
        return {}

    if not hard_constraints:
        logger.info("Safety pre-filter: no allergens to expand")
        return {"safety_check_passed": True, "safety_violations": []}

    expanded = expand_allergens(hard_constraints)
    logger.info(
        "Safety pre-filter expanded allergens",
        original=hard_constraints,
        expanded_count=len(expanded),
    )

    return {
        "hard_constraints": expanded,
        "safety_check_passed": True,
        "safety_violations": [],
    }


async def safety_constraint_node(state: AgentState) -> dict:
    logger.info("Safety constraint check invoked")

    hard_constraints = state.get("hard_constraints", [])
    product_results = state.get("product_results", [])

    if not hard_constraints or not product_results:
        return {
            "safety_check_passed": True,
            "safety_violations": [],
        }

    safe_products = []
    violations = []

    # Gate 1: Rule-based filtering
    for product in product_results:
        ingredients = product.get("ingredients", [])
        if isinstance(ingredients, str):
            ingredients = parse_ingredients(ingredients)

        matches = find_allergen_matches(ingredients, hard_constraints)
        if matches:
            violations.append(
                {
                    "product": product.get("name", "Unknown"),
                    "matches": matches,
                    "gate": "rule_based",
                }
            )
            logger.info(
                "Product vetoed by rule-based gate",
                product=product.get("name"),
                matches=matches,
            )
        else:
            safe_products.append(product)

    # Gate 2: LLM post-check on remaining products (catches synonyms)
    if safe_products and hard_constraints:
        try:
            llm = get_llm(temperature=0)
            products_text = "\n".join(
                f"- {p.get('name', 'Unknown')}: {', '.join(p.get('ingredients', [])[:30])}"
                for p in safe_products
            )
            response = await llm.ainvoke(
                [
                    SystemMessage(
                        content=SAFETY_LLM_PROMPT.format(
                            allergies=", ".join(hard_constraints),
                            products=products_text,
                        )
                    ),
                    HumanMessage(content="Check these products for safety."),
                ]
            )

            # Parse LLM response for any UNSAFE flags
            safety_content = (
                response.content if isinstance(response.content, str) else str(response.content)
            )
            for line in safety_content.split("\n"):
                if "UNSAFE" in line.upper():
                    for product in safe_products[:]:
                        if product.get("name", "").lower() in line.lower():
                            safe_products.remove(product)
                            violations.append(
                                {
                                    "product": product.get("name"),
                                    "reason": line.strip(),
                                    "gate": "llm_check",
                                }
                            )
        except Exception as e:
            logger.error("LLM safety check failed, keeping rule-based results", error=str(e))

    all_vetoed = len(safe_products) == 0 and len(product_results) > 0

    return {
        "product_results": safe_products,
        "safety_check_passed": not all_vetoed,
        "safety_violations": violations,
    }


def _normalize_for_override_check(message: str) -> str:
    """Normalize a message for override detection.

    Collapses whitespace, lowercases, and strips punctuation noise
    while preserving word boundaries for accurate matching.
    """
    text = message.lower()
    # Normalize curly/smart apostrophes to straight
    text = text.replace("\u2019", "'").replace("\u2018", "'")
    # Collapse whitespace (tabs, newlines, multiple spaces)
    text = re.sub(r"\s+", " ", text).strip()
    # Remove punctuation except apostrophes (needed for contractions like "don't")
    text = re.sub(r"[^\w\s']", " ", text)
    # Re-collapse whitespace after punctuation removal
    text = re.sub(r"\s+", " ", text).strip()
    return text


# Pre-compiled regex patterns for override detection.
# Uses word boundaries (\b) to avoid false positives on partial matches.
_OVERRIDE_PATTERNS: list[re.Pattern[str]] = [
    p
    for p in [
        # "show/give/list ... anyway" — catches "show it anyway", "give me them anyway", etc.
        re.compile(r"\b(?:show|give|list|recommend|tell)\b.{0,30}\banyway\b"),
        # "ignore my allerg(y|ies) / sensitivity / sensitivities"
        re.compile(r"\bignore\b.{0,15}\b(?:allerg|sensitiv)"),
        # "override safety/allergy/filter/check"
        re.compile(r"\boverride\b.{0,15}\b(?:safety|allerg|filter|check)"),
        # "bypass safety/allergy/filter/check"
        re.compile(r"\bbypass\b.{0,15}\b(?:safety|allerg|filter|check)"),
        # "skip the/my safety/allergy/check/filter"
        re.compile(r"\bskip\b.{0,15}\b(?:safety|allerg|filter|check)"),
        # "disable safety/allergy/filter/check"
        re.compile(r"\bdisable\b.{0,15}\b(?:safety|allerg|filter|check)"),
        # "turn off safety/allergy/filter/check"
        re.compile(r"\bturn\s+off\b.{0,15}\b(?:safety|allerg|filter|check)"),
        # "i'll take the risk" / "willing to risk it"
        re.compile(r"\b(?:i'?ll|i\s+will|willing\s+to)\b.{0,15}\b(?:take|accept)\b.{0,10}\brisk"),
        # "don't/doesn't care about allerg(y|ies)/safety/ingredients"
        re.compile(r"\bdon'?t\s+care\b.{0,15}\b(?:allerg|safety|sensitiv|ingredient|reaction)"),
        # "i don't have allergies" (lying about allergies to bypass)
        re.compile(r"\bi\s+(?:don'?t|do\s+not)\s+(?:actually\s+)?have\b.{0,10}\ballerg"),
        # "show the unsafe ones/products"
        re.compile(r"\bshow\b.{0,15}\bunsafe\b"),
        # "just give me all/every product(s)"
        re.compile(r"\bjust\s+give\b.{0,15}\b(?:all|every)\b.{0,10}\bproduct"),
        # "include the unsafe/flagged/blocked/filtered products"
        re.compile(r"\b(?:include|add)\b.{0,15}\b(?:unsafe|flagged|blocked|filtered|removed)\b"),
        # "remove my allerg(y|ies) / constraints / restrictions"
        re.compile(
            r"\b(?:remove|delete|clear)\b.{0,15}"
            r"\b(?:my\s+)?(?:allerg|constraint|restriction|safety\s+(?:filter|check))"
        ),
        # "forget my allerg(y|ies)" (trying to erase safety data)
        re.compile(r"\bforget\b.{0,15}\b(?:my\s+)?allerg"),
        # "pretend i'm not allergic / pretend i have no allergies"
        re.compile(r"\bpretend\b.{0,15}\b(?:not\s+allergic|no\s+allerg)"),
        # "i'm not really/actually allergic"
        re.compile(r"\bnot\s+(?:really|actually)\s+allergic\b"),
        # "stop filtering / stop blocking / stop checking"
        re.compile(r"\bstop\b.{0,10}\b(?:filter|block|check|flag)"),
        # "show me everything / show all products regardless"
        re.compile(r"\b(?:show|give|list)\b.{0,15}\b(?:everything|all)\b.{0,15}\bregardless\b"),
    ]
]


def check_override_attempt(message: str) -> bool:
    """Detect if a user message is attempting to override safety constraints.

    Uses normalized text and regex patterns with word boundaries to catch
    override attempts while minimizing false positives on legitimate messages.
    """
    normalized = _normalize_for_override_check(message)
    return any(pattern.search(normalized) for pattern in _OVERRIDE_PATTERNS)
