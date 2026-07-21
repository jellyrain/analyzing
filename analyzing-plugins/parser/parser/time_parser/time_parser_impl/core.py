from __future__ import annotations

import re
from typing import Literal


class HighPrecisionTimeParserCore:
    """
    高精度时间提取逻辑
    """

    def __init__(self) -> None:
        self.date_req = re.compile(r"(\d{4})[-年](\d{1,2})[-月](\d{1,2})[日]?")
        self.time_req = re.compile(r"(\d{1,2})[:：点时](\d{2})(?:[:：分](\d{2})[秒]?)?")

    def parse(
        self,
        text: str,
        keyword: str,
        window_size: int = 100,
        direction: Literal["front", "back"] | None = None,
    ) -> list[dict[str, str]]:
        date_matches = list(self.date_req.finditer(text))
        dates_map: list[tuple[int, str]] = []
        for match in date_matches:
            y, mo, d = match.groups()
            dates_map.append((match.start(), f"{y}-{mo.zfill(2)}-{d.zfill(2)}"))

        if not dates_map:
            return []

        key_matches = list(re.finditer(re.escape(keyword), text))
        results: list[dict[str, str]] = []
        for keyword_match in key_matches:
            key_start = keyword_match.start()
            search_start = max(0, key_start - window_size)
            search_end = min(len(text), keyword_match.end() + 20)
            context = text[search_start:search_end]
            time_matches = list(self.time_req.finditer(context))
            if not time_matches:
                continue

            times_before: list[tuple[int, str, int, bool]] = []
            times_after: list[tuple[int, str, int, bool]] = []
            for time_match in time_matches:
                h, m, s = time_match.groups()
                has_seconds = s is not None
                second_value = s.zfill(2) if s is not None else "00"
                formatted_time = f"{h.zfill(2)}:{m.zfill(2)}:{second_value}"
                abs_pos = search_start + time_match.start()
                match_info = (
                    abs(abs_pos - key_start),
                    formatted_time,
                    abs_pos,
                    has_seconds,
                )
                if abs_pos <= key_start:
                    times_before.append(match_info)
                else:
                    times_after.append(match_info)

            best_match: tuple[int, str, int, bool] | None = None
            if direction == "front":
                if times_before:
                    best_match = min(times_before, key=lambda item: item[0])
                elif times_after:
                    best_match = min(times_after, key=lambda item: item[0])
            elif direction == "back":
                if times_after:
                    best_match = min(times_after, key=lambda item: item[0])
                elif times_before:
                    best_match = min(times_before, key=lambda item: item[0])
            else:
                candidates = times_before + times_after
                if candidates:
                    best_match = min(candidates, key=lambda item: item[0])

            if best_match is None:
                continue

            _, best_time_str, best_time_abs_pos, has_seconds = best_match
            target_date = dates_map[0][1]
            for date_idx, date_value in reversed(dates_map):
                if date_idx < best_time_abs_pos:
                    target_date = date_value
                    break

            results.append(
                {
                    "keyword": keyword,
                    "full_datetime": f"{target_date} {best_time_str}",
                    "raw_context": context.replace("\n", " ").strip(),
                    "precision": "second" if has_seconds else "minute",
                }
            )

        return results


__all__ = ["HighPrecisionTimeParserCore"]
