from __future__ import annotations

import re


class KVParserCore:
    """
    KV 提取逻辑
    """

    @staticmethod
    def parse(
        text: str,
        separator_chars: str = ":：",
        allow_multiline: bool = False,
        punct_chars: str = r"\s,;，；。、",
        allow_key_start_with_digit: bool = False,
    ) -> dict[str, list[str]]:
        if not text:
            return {}

        result: dict[str, list[str]] = {}
        sep_chars = separator_chars or ":："

        if allow_key_start_with_digit:
            key_pattern = rf"[^{punct_chars}{sep_chars}][^{punct_chars}{sep_chars}]*"
        else:
            key_pattern = rf"[^\d{punct_chars}{sep_chars}][^{punct_chars}{sep_chars}]*"

        sep_pattern = rf"[{sep_chars}]"

        kv_regex = re.compile(
            rf"(?:^|[{punct_chars}]+)"
            rf"({key_pattern})"
            rf"\s*{sep_pattern}\s*"
            rf"(.*?)"
            rf"(?=$|[{punct_chars}]+{key_pattern}\s*{sep_pattern}|[{punct_chars}]+$)",
            re.DOTALL if allow_multiline else 0,
        )

        target_texts = [text] if allow_multiline else text.split("\n")

        for section in target_texts:
            section = section.strip()
            if not section:
                continue

            for match in kv_regex.finditer(section):
                key = match.group(1).strip()
                value = match.group(2).strip()
                value = re.sub(rf"[{punct_chars}]+$", "", value).strip()

                if key and value:
                    result.setdefault(key, []).append(value)

        return result


__all__ = ["KVParserCore"]
