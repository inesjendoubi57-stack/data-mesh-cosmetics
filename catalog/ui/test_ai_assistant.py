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
    response = Mock(text="Le contrat reste compatible.")
    client = Mock()
    client.models.generate_content.return_value = response

    with patch.dict("os.environ", {"GEMINI_API_KEY": "test-key"}):
        with patch.object(ai_assistant.genai, "Client", return_value=client) as create_client:
            result = ai_assistant.explain_changes(DIFF)

    create_client.assert_called_once_with(api_key="test-key")
    client.models.generate_content.assert_called_once()
    assert client.models.generate_content.call_args.kwargs["model"] == ai_assistant.MODEL
    assert result == {"text": "Le contrat reste compatible.", "by_ai": True}


def test_explain_changes_uses_plain_notes_without_key():
    with patch.dict("os.environ", {}, clear=True):
        with patch.object(ai_assistant.genai, "Client") as create_client:
            result = ai_assistant.explain_changes(DIFF)

    create_client.assert_not_called()
    assert result == {"text": ai_assistant.plain_notes(DIFF), "by_ai": False}
