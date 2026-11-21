import json
import logging
import os
import time
import requests

MODEL = os.environ.get("LLM_MODEL", "gemini-3.8-flash")
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
logger = logging.getLogger("ai_assistant")

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


def ask_gemini(diff, api_key):
    body = {
        "system_instruction": {"parts": [{"text": SYSTEM}]},
        "contents": [{"parts": [{"text": json.dumps(diff, ensure_ascii=False)}]}],
    }

    # 503 / 429 : le modèle est surchargé, on réessaie deux fois avant d'abandonner
    for attempt in range(3):
        response = requests.post(
            API_URL.format(model=MODEL),
            headers={"x-goog-api-key": api_key},
            json=body,
            timeout=30,
        )
        if response.status_code not in (429, 500, 503):
            break
        time.sleep(2 * (attempt + 1))

    if response.status_code != 200:
        raise RuntimeError(f"HTTP {response.status_code} : {response.text[:300]}")

    parts = response.json()["candidates"][0]["content"]["parts"]
    return "".join(part.get("text", "") for part in parts).strip()


def explain_changes(diff):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return {"text": plain_notes(diff), "by_ai": False}

    try:
        text = ask_gemini(diff, api_key)
    except Exception as error:
        # L'IA est optionnelle : la page doit s'afficher même si l'appel échoue.
        logger.warning("Assistant IA indisponible : %s", error)
        return {"text": plain_notes(diff), "by_ai": False}

    if not text:
        return {"text": plain_notes(diff), "by_ai": False}
    return {"text": text, "by_ai": True}
