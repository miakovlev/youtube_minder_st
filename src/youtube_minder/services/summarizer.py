import openai


def summarize_text(text: str, language: str = "en") -> str:
    """
    Summarizes the given text using gpt-4o-mini.

    :param text: The transcription text to summarize.
    :param language: The target language for the summary ('en' or 'ru').
    """
    client = openai.OpenAI()

    lang_instruction = "in English" if language == "en" else "in Russian"

    prompt = (
        f"Summarize the following video transcription {lang_instruction}. "
        "Identify the main topic, key points, and conclusion.\n\n"
        f"{text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are a helpful assistant that summarizes video transcriptions."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content
