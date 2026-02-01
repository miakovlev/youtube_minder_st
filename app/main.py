import sys


def main() -> None:
    message = (
        "Telegram bot entrypoint is deprecated. "
        "Run the Streamlit app instead: streamlit run src/youtube_minder/ui/streamlit_app.py"
    )
    print(message, file=sys.stderr)


if __name__ == "__main__":
    main()
