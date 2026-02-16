import structlog
from langchain_core.messages import HumanMessage, SystemMessage

from app.agents.state import AgentState
from app.catalog.ingredient_parser import find_allergen_matches, parse_ingredients
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
                f"- {p.get('name', 'Unknown')}: {', '.join(p.get('ingredients', [])[:15])}"
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


def check_override_attempt(message: str) -> bool:
    override_phrases = [
        "show it anyway",
        "just show me",
        "i don't care",
        "show me anyway",
        "ignore my allergies",
        "override",
        "i'll take the risk",
    ]
    lower = message.lower()
    return any(phrase in lower for phrase in override_phrases)
