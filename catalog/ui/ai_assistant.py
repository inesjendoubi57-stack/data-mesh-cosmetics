import json
import os

import anthropic

MODEL = os.environ.get("LLM_MODEL", "claude-opus-5-5")

SYSTEM = (
    "Tu aides des analystes BI à suivre l'évolution d'un data contract. "
    "On te donne le résultat exact de la comparaison entre le contrat actif et une "
    "version proposée, calculé par le compatibility checker. "
    "Rédige en français des notes de migration courtes : ce qui change, puis ce que "
    "le consommateur doit faire. Appuie-toi uniquement sur cette comparaison, n'ajoute "
    "aucun changement qui n'y figure pas. Texte simple, sans markdown."
)

ADVICE = {
    "COMPATIBLE": "Rien à modifier côté consommateur.",
    "REVIEW_REQUIRED": "Pas de casse attendue, mais un reviewer doit valider ce changement.",
    "INCOMPATIBLE": "Les requêtes et dashboards qui lisent ces champs doivent être adaptés avant de migrer.",
}


def plain_notes(diff):
    lines = [f"{diff['contract']} : {diff['old_version']} -> {diff['new_version']}"]
    if not diff["changes"]:
        lines.append("Aucun changement.")
    for change in diff["changes"]:
        lines.append(f"- {change}")
    lines.append(ADVICE[diff["status"]])
    return "\n".join(lines)


def explain_changes(diff):
    if not os.environ.get("ANTHROPIC_API_KEY"):
        return {"text": plain_notes(diff), "by_ai": False}

    try:
        response = anthropic.Anthropic().beta.messages.create(
            model=MODEL,
            max_tokens=2000,
            betas=["server-side-fallback-2026-07-01"],
            fallbacks="default",
            system=SYSTEM,
            messages=[{"role": "user", "content": json.dumps(diff, ensure_ascii=False)}],
        )
    except anthropic.APIError:
        return {"text": plain_notes(diff), "by_ai": False}

    text = "".join(block.text for block in response.content if block.type == "text").strip()
    if response.stop_reason == "refusal" or not text:
        return {"text": plain_notes(diff), "by_ai": False}
    return {"text": text, "by_ai": True}
