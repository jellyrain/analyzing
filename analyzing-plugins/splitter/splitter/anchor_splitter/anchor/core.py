from __future__ import annotations

import re


class AnchorTextSplit:
    """负责按锚点切分文本"""

    @staticmethod
    def split_by_anchor(
        text: str,
        anchor_start: str,
        anchor_end: str | None = None,
        is_regex: bool = False,
    ) -> list[str]:
        """
        按锚点切分
        """

        if is_regex:
            if anchor_end:
                pattern = rf"(?:{anchor_start})(?P<content>.*?)(?:{anchor_end})"
            else:
                pattern = rf"(?:{anchor_start})(?P<content>.*)"

            try:
                matches = re.finditer(pattern, text, re.DOTALL)
            except re.error:
                return []

            return [
                match.group("content").strip()
                for match in matches
                if match.group("content").strip()
            ]

        if anchor_end:
            parts = text.split(anchor_start)
            chunks: list[str] = []

            for part in parts[1:]:
                if anchor_end in part:
                    chunk = part.split(anchor_end)[0].strip()
                    if chunk:
                        chunks.append(chunk)

            return chunks

        parts = text.split(anchor_start)
        return [part.strip() for part in parts[1:] if part.strip()]


__all__ = ["AnchorTextSplit"]
