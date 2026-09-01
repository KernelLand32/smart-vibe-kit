"""Convert interview answers into a deterministic project profile."""

from .constants import CORE_DOCUMENTS, MODULES, MODULE_DOCUMENTS, VERSION
from .util import slugify


REQUIRED_BY_SIGNAL = {
    "user_facing": ("product",),
    "ui": ("product", "design"),
    "deployable": ("engineering", "operations"),
    "sensitive_data": ("security",),
    "regulated": ("research", "security", "regulated"),
}

LIST_FIELDS = (
    "goals",
    "non_goals",
    "constraints",
    "platforms",
    "integrations",
    "include_modules",
    "exclude_modules",
)


def _integer_answer(answers, name, default, minimum, maximum=None):
    value = answers.get(name, default)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("%s must be an integer." % name)
    if value < minimum or (maximum is not None and value > maximum):
        if maximum is None:
            raise ValueError("%s must be at least %d." % (name, minimum))
        raise ValueError("%s must be between %d and %d." % (name, minimum, maximum))
    return value


def _validate_answers(answers):
    if not isinstance(answers, dict):
        raise ValueError("Interview answers must be a JSON object.")
    for name in REQUIRED_BY_SIGNAL:
        if name in answers and not isinstance(answers[name], bool):
            raise ValueError("%s must be true or false." % name)
    for name in LIST_FIELDS:
        value = answers.get(name, [])
        if value is None:
            continue
        if not isinstance(value, list) or any(not isinstance(item, str) or not item.strip() for item in value):
            raise ValueError("%s must be an array of non-empty strings." % name)
    _integer_answer(answers, "team_size", 1, 1)
    _integer_answer(answers, "research_tier", 0, 0, 3)
    risk = str(answers.get("risk", "normal")).lower()
    if risk not in ("low", "normal", "high"):
        raise ValueError("risk must be low, normal, or high.")
    includes = set(answers.get("include_modules", []) or [])
    excludes = set(answers.get("exclude_modules", []) or [])
    overlap = includes & excludes
    if overlap:
        raise ValueError("Modules cannot be both included and excluded: %s" % ", ".join(sorted(overlap)))


def select_modules(answers):
    _validate_answers(answers)
    selected = {"core"}
    for signal, modules in REQUIRED_BY_SIGNAL.items():
        if bool(answers.get(signal, False)):
            selected.update(modules)
    if _integer_answer(answers, "research_tier", 0, 0, 3) > 0:
        selected.add("research")
    if answers.get("integrations"):
        selected.add("engineering")
    if _integer_answer(answers, "team_size", 1, 1) > 1:
        selected.add("collaboration")

    required = set(selected)
    includes = set(answers.get("include_modules", []) or [])
    excludes = set(answers.get("exclude_modules", []) or [])
    unknown = (includes | excludes) - set(MODULES)
    if unknown:
        raise ValueError("Unknown modules: %s" % ", ".join(sorted(unknown)))
    selected.update(includes)

    selected -= (excludes - required)
    return [module for module in MODULES if module in selected]


def profile_name(modules, answers):
    module_set = set(modules)
    if "regulated" in module_set:
        return "regulated"
    risk = str(answers.get("risk", "normal")).lower()
    if risk == "high" or len(modules) >= 7:
        return "extended"
    if len(modules) <= 2 and risk == "low":
        return "lean"
    return "standard"


def expected_document_count(modules):
    # Human documents plus profile, state, plan, verifiers, governance, evidence,
    # installation provenance, and the durable Interview checkpoint.
    machine_files = 8
    return len(CORE_DOCUMENTS) + machine_files + sum(
        len(MODULE_DOCUMENTS.get(module, ())) for module in modules
    )


def build_profile(answers):
    _validate_answers(answers)
    title = str(answers.get("title", "")).strip()
    idea = str(answers.get("idea", "")).strip()
    if not title:
        raise ValueError("A project title is required.")
    if not idea:
        raise ValueError("A project idea is required.")
    modules = select_modules(answers)
    return {
        "schema_version": "2.1",
        "svk_version": VERSION,
        "title": title,
        "slug": slugify(answers.get("slug") or title),
        "idea": idea,
        "goals": list(answers.get("goals", []) or []),
        "non_goals": list(answers.get("non_goals", []) or []),
        "constraints": list(answers.get("constraints", []) or []),
        "platforms": list(answers.get("platforms", []) or []),
        "integrations": list(answers.get("integrations", []) or []),
        "research_tier": _integer_answer(answers, "research_tier", 0, 0, 3),
        "risk": str(answers.get("risk", "normal")).lower(),
        "team_size": _integer_answer(answers, "team_size", 1, 1),
        "signals": {
            name: bool(answers.get(name, False)) for name in REQUIRED_BY_SIGNAL
        },
        "profile": profile_name(modules, answers),
        "modules": modules,
        "expected_document_count": expected_document_count(modules),
    }
