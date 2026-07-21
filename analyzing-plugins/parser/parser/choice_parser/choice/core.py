from __future__ import annotations

import re


class ChoiceParserCore:
    """
    选项提取逻辑
    """

    @staticmethod
    def parse(
        text: str,
        markers: list[str],
        allow_multiline: bool = False,
        is_suffix_marker: bool = False,
        strip_chars: str = "",
    ) -> dict[str, list[str]]:
        if not text or not markers:
            return {}

        result: dict[str, list[str]] = {}
        escaped_markers = [re.escape(marker) for marker in markers]
        escaped_markers.sort(key=len, reverse=True)
        markers_pattern = f"({'|'.join(escaped_markers)})"

        if not is_suffix_marker:
            choice_regex = re.compile(
                rf"{markers_pattern}(.*?)" rf"(?={markers_pattern}|$)",
                re.DOTALL if allow_multiline else 0,
            )
        else:
            choice_regex = re.compile(
                rf"(.*?)" rf"{markers_pattern}",
                re.DOTALL if allow_multiline else 0,
            )

        target_texts = [text] if allow_multiline else text.split("\n")
        chars_to_strip = " \t\n\r" + strip_chars
        for section in target_texts:
            section = section.strip()
            if not section:
                continue

            for match in choice_regex.finditer(section):
                if not is_suffix_marker:
                    marker = match.group(1).strip()
                    value = match.group(2).strip(chars_to_strip)
                else:
                    value = match.group(1).strip(chars_to_strip)
                    marker = match.group(2).strip()

                if value:
                    result.setdefault(marker, []).append(value)

        return result


__all__ = ["ChoiceParserCore"]
