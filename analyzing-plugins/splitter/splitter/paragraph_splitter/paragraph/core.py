class ParagraphTextSplit:
    """负责按段落切分文本"""

    @staticmethod
    def split_by_paragraph(text: str) -> list[str]:
        """
        按双换行切分段落
        """

        return [item.strip() for item in text.split("\n\n") if item.strip()]


__all__ = ["ParagraphTextSplit"]
