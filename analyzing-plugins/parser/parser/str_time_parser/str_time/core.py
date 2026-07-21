from __future__ import annotations

import re


class StrTimeParserCore:
    """
    字符串时间提取逻辑
    """

    def __init__(self) -> None:
        digit = r"\d+|[零〇一二两三四五六七八九十]+"
        self.date_req = rf"({digit})\s*[-年./]\s*({digit})\s*[-月./]\s*({digit})\s*[日号]?"
        self.time_req = (
            rf"(上午|早上|凌晨|中午|下午|晚上|傍晚)?\s*({digit})\s*"
            rf"(?:[:：]\s*({digit})(?:\s*[:：]\s*({digit})\s*[秒]?)?|"
            rf"[点时](?:\s*({digit})\s*分?(?:\s*({digit})\s*秒)?)?)"
        )

    @staticmethod
    def chinese_to_int(value: str) -> int:
        value = value.strip()
        if value.isdigit():
            return int(value)

        num_map = {
            "零": 0,
            "〇": 0,
            "一": 1,
            "二": 2,
            "两": 2,
            "三": 3,
            "四": 4,
            "五": 5,
            "六": 6,
            "七": 7,
            "八": 8,
            "九": 9,
        }

        if "十" not in value:
            return int("".join(str(num_map[ch]) for ch in value))

        if value == "十":
            return 10

        tens, _, ones = value.partition("十")
        tens_value = num_map[tens] if tens else 1
        ones_value = num_map[ones] if ones else 0
        return tens_value * 10 + ones_value

    @classmethod
    def fmt_d(cls, d_tuple: tuple[str, str, str]) -> str:
        year = cls.chinese_to_int(d_tuple[0])
        month = cls.chinese_to_int(d_tuple[1])
        day = cls.chinese_to_int(d_tuple[2])
        return f"{year}-{month:02d}-{day:02d}"

    @classmethod
    def fmt_t(cls, t_tuple: tuple[str, str, str, str, str, str]) -> tuple[str, bool]:
        period, hour_text, colon_minute, colon_second, zh_minute, zh_second = t_tuple
        minute_text = colon_minute or zh_minute
        second_text = colon_second or zh_second
        hour = cls.chinese_to_int(hour_text)
        minute = cls.chinese_to_int(minute_text) if minute_text else 0
        second = cls.chinese_to_int(second_text) if second_text and second_text.strip() else 0

        if period in {"下午", "晚上", "傍晚"} and hour < 12:
            hour += 12
        elif period == "中午" and hour < 11:
            hour += 12
        elif period == "凌晨" and hour == 12:
            hour = 0

        return f"{hour:02d}:{minute:02d}:{second:02d}", bool(
            second_text and second_text.strip()
        )

    def parse(self, text: str) -> list[dict[str, str]]:
        date_matches = re.findall(self.date_req, text)
        time_matches = re.findall(self.time_req, text)
        formatted_dates = [self.fmt_d(d) for d in date_matches]
        formatted_times = [self.fmt_t(t) for t in time_matches]

        if not formatted_dates and not formatted_times:
            return []

        if not formatted_times:
            return [
                {
                    "full_datetime": f"{date_value} 00:00:00",
                    "raw_context": text.replace("\n", " ").strip(),
                    "precision": "day",
                }
                for date_value in formatted_dates
            ]

        results: list[dict[str, str]] = []
        for index, time_item in enumerate(formatted_times):
            current_date = (
                formatted_dates[index] if index < len(formatted_dates) else formatted_dates[0]
            ) if formatted_dates else "1970-01-01"
            results.append(
                {
                    "full_datetime": f"{current_date} {time_item[0]}",
                    "raw_context": text.replace("\n", " ").strip(),
                    "precision": "second" if time_item[1] else "minute",
                }
            )

        return results


__all__ = ["StrTimeParserCore"]
