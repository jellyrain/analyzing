class WindowTextSplit:
    """负责按滑动窗口切分文本"""

    @staticmethod
    def split_by_window(
        text: str,
        window_size: int = 512,
        overlap: int = 128,
    ) -> list[str]:
        """
        按滑动窗口切分
        """

        if len(text) <= window_size:
            return [text]

        chunks: list[str] = []
        start = 0
        step = window_size - overlap

        while start < len(text):
            end = min(start + window_size, len(text))
            chunks.append(text[start:end])

            if end == len(text):
                break

            start += step

        return chunks


__all__ = ["WindowTextSplit"]
