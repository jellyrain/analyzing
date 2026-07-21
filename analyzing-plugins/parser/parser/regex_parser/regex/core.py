from __future__ import annotations

import re


class RegexParserCore:
    """
    正则提取逻辑
    """

    @staticmethod
    def parse(
        text: str,
        pattern: str,
        group_index: int = 1,
        negative_pattern: str | None = None,
    ) -> list[str]:
        if not text or not pattern:
            return []

        try:
            regex = re.compile(pattern)
            neg_regex = re.compile(negative_pattern) if negative_pattern else None
        except re.error:
            return []

        results: list[str] = []
        for match in regex.finditer(text):
            if match.lastindex and group_index <= match.lastindex:
                content = match.group(group_index).strip()
            else:
                content = match.group(0).strip()

            if neg_regex:
                start_pos = max(0, match.start() - 5)
                pre_text = text[start_pos : match.start()]
                if neg_regex.search(pre_text):
                    continue

            if content:
                results.append(content)

        return list(dict.fromkeys(results))


__all__ = ["RegexParserCore"]
