from __future__ import annotations

import re


class BracketKVParserCore:
    """
    括号键值提取逻辑
    """

    @staticmethod
    def parse(
        text: str,
        left_bracket: str = "【",
        right_bracket: str = "】",
        allow_multiline: bool = False,
    ) -> dict[str, list[str]]:
        if not text:
            return {}

        result: dict[str, list[str]] = {}
        bracket_kv_regex = re.compile(
            rf"{re.escape(left_bracket)}(.*?){re.escape(right_bracket)}"
            rf"(.*?)"
            rf"(?={re.escape(left_bracket)}|$)",
            re.DOTALL if allow_multiline else 0,
        )

        target_texts = [text] if allow_multiline else text.split("\n")
        for section in target_texts:
            section = section.strip()
            if not section:
                continue

            for match in bracket_kv_regex.finditer(section):
                key = match.group(1).strip()
                value = match.group(2).strip()
                if key and value:
                    result.setdefault(key, []).append(value)

        return result


__all__ = ["BracketKVParserCore"]
