import os
import json
from google.cloud import dialogflow
from google.oauth2 import service_account


def detect_intent(text: str, session_id: str = "user123", language_code: str = "th") -> dict:
    credentials_json = os.environ.get("GOOGLE_CREDENTIALS")
    if not credentials_json:
        raise ValueError("[DIALOGFLOW] GOOGLE_CREDENTIALS env var is not set")

    try:
        credentials_dict = json.loads(credentials_json)
    except json.JSONDecodeError as e:
        raise ValueError(f"[DIALOGFLOW] GOOGLE_CREDENTIALS is not valid JSON: {e}")

    project_id = credentials_dict.get("project_id")
    if not project_id:
        raise ValueError("[DIALOGFLOW] project_id not found in GOOGLE_CREDENTIALS")

    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict,
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    session_client = dialogflow.SessionsClient(credentials=credentials)
    session = session_client.session_path(project_id, session_id)

    text_input  = dialogflow.TextInput(text=text, language_code=language_code)
    query_input = dialogflow.QueryInput(text=text_input)

    response = session_client.detect_intent(
        request={"session": session, "query_input": query_input}
    )

    return {
        "intent":           response.query_result.intent.display_name,
        "parameters":       dict(response.query_result.parameters),
        "fulfillment_text": response.query_result.fulfillment_text,
        "confidence":       response.query_result.intent_detection_confidence,
    }
