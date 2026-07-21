from __future__ import annotations

import re


class RegexTextSplit:
    """负责按正则切分文本"""

    @staticmethod
    def split_by_regex(text: str, pattern: str) -> list[str]:
        """
        按正则切分
        """

        return [item.strip() for item in re.split(pattern, text) if item.strip()]


__all__ = ["RegexTextSplit"]
