from unittest.mock import Mock, patch

from catalog.ui import ai_assistant


DIFF = {
    "contract": "products",
    "old_version": "1.0",
    "new_version": "1.1",
    "status": "COMPATIBLE",
    "changes": [],
}


def test_explain_changes_uses_gemini_when_key_is_configured():
    response = Mock(status_code=200)
    response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Le contrat reste compatible."}]}}]
    }

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with patch.object(ai_assistant.requests, "post", return_value=response) as post:
            result = ai_assistant.explain_changes(DIFF)

    post.assert_called_once()
    assert post.call_args.kwargs["headers"] == {"x-goog-api-key": "test-key"}
    assert result == {"text": "Le contrat reste compatible.", "by_ai": True}


def test_explain_changes_uses_plain_notes_without_key():
    with patch.dict("os.environ", {}, clear=True):
        with patch.object(ai_assistant.requests, "post") as post:
            result = ai_assistant.explain_changes(DIFF)

    post.assert_not_called()
    assert result == {"text": ai_assistant.plain_notes(DIFF), "by_ai": False}