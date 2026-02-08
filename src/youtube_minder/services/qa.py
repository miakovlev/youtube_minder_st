import openai


def answer_questions(transcription_text: str, questions: list[str]) -> str:
    """
    Answer questions about a video transcript. Replies use the same language as each question.
    """
    client = openai.OpenAI()

    questions_block = "\n".join(f"{idx + 1}. {q}" for idx, q in enumerate(questions))
    prompt = (
        "Answer the questions about the video transcript. "
        "Answer each question in the same language as the question. "
        "If the transcript does not contain the answer, say so briefly.\n\n"
        f"Questions:\n{questions_block}\n\n"
        f"Transcript:\n{transcription_text}"
    )

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You answer questions about video transcripts."},
            {"role": "user", "content": prompt},
        ],
    )

    return response.choices[0].message.content
