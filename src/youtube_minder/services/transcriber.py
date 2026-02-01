import openai


def transcribe_openai(file_path: str, model_name: str = "gpt-4o-mini-transcribe") -> str:
    """
    Transcribes an audio file using OpenAI Whisper API (gpt-4o-mini-transcribe).
    """
    client = openai.OpenAI()
    with open(file_path, "rb") as audio_file:
        transcription = client.audio.transcriptions.create(
            model=model_name,
            file=audio_file,
            response_format="text",
        )
    return transcription
