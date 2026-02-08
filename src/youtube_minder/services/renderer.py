from pathlib import Path


class HTMLRenderer:
    def __init__(self, wrapper_path: Path) -> None:
        self.wrapper_path = wrapper_path
        self._wrapper_html: str | None = None

    def _load_wrapper(self) -> str:
        if self._wrapper_html is None:
            self._wrapper_html = self.wrapper_path.read_text(encoding="utf-8")
        return self._wrapper_html

    def render(self, html_body: str) -> bytes:
        wrapper = self._load_wrapper()
        full_html = wrapper.replace("{{CONTENT}}", html_body)

        try:
            import pydyf
            from weasyprint import HTML
        except Exception as exc:
            raise RuntimeError("WeasyPrint is required to render PDFs. Install weasyprint.") from exc

        if not hasattr(pydyf.Stream, "transform") and hasattr(pydyf.Stream, "set_matrix"):
            def _transform(self, a=1, b=0, c=0, d=1, e=0, f=0):
                return self.set_matrix(a, b, c, d, e, f)

            pydyf.Stream.transform = _transform

        if not hasattr(pydyf.Stream, "text_matrix") and hasattr(pydyf.Stream, "set_text_matrix"):
            def _text_matrix(self, a=1, b=0, c=0, d=1, e=0, f=0):
                return self.set_text_matrix(a, b, c, d, e, f)

            pydyf.Stream.text_matrix = _text_matrix

        doc = HTML(string=full_html, base_url=str(self.wrapper_path.parent)).render()
        return doc.write_pdf()
