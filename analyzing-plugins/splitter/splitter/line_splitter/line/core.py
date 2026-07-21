class LineTextSplit:
    """负责把长文本按行切成小份"""

    @staticmethod
    def split_by_line(text: str) -> list[str]:
        """
        按行切分
        """

        return [line.strip() for line in text.split("\n") if line.strip()]


__all__ = ["LineTextSplit"]
