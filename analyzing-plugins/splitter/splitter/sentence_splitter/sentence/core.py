from __future__ import annotations

import re


class SentenceTextSplit:
    """负责按句子切分文本"""

    @staticmethod
    def split_by_sentence(text: str) -> list[str]:
        """
        按句末标点切分
        """

        pattern = r"([。！？；……]+)"
        parts = re.split(pattern, text)
        sentences: list[str] = []

        for index in range(0, len(parts) - 1, 2):
            sentence = parts[index].strip() + parts[index + 1].strip()
            if sentence:
                sentences.append(sentence)

        if len(parts) % 2 != 0:
            last_part = parts[-1].strip()
            if last_part:
                sentences.append(last_part)

        return sentences


__all__ = ["SentenceTextSplit"]
