from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation


class StrNumberParserCore:
    """
    字符串数字提取逻辑
    """

    _FULLWIDTH_TRANS = str.maketrans(
        {
            "０": "0",
            "１": "1",
            "２": "2",
            "３": "3",
            "４": "4",
            "５": "5",
            "６": "6",
            "７": "7",
            "８": "8",
            "９": "9",
            "．": ".",
            "，": ",",
            "＋": "+",
            "－": "-",
            "％": "%",
        }
    )
    _CHINESE_DIGITS = {
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
    _CHINESE_UNITS = {"十": 10, "百": 100, "千": 1000}
    _CHINESE_SECTION_UNITS = {"万": 10000, "亿": 100000000}
    _CHINESE_NUM_CHARS = "零〇一二两三四五六七八九十百千万亿"
    _CHINESE_DECIMAL_CHARS = "零〇一二两三四五六七八九"

    def __init__(self) -> None:
        arabic_core = r"(?:\d{1,3}(?:,\d{3})+|\d+)(?:\.\d+)?|\.\d+"
        scientific_suffix = r"(?:\s*(?:[eE][+-]?\d+|[×xX*]\s*10\^?\s*[+-]?\d+))?"
        chinese_number = (
            rf"(?:负|零下)?[{self._CHINESE_NUM_CHARS}]+"
            rf"(?:点[{self._CHINESE_DECIMAL_CHARS}]+)?"
        )
        token = rf"\d+|[{self._CHINESE_NUM_CHARS}]+"

        self.arabic_percent_req = re.compile(rf"[+-]?(?:{arabic_core})\s*%")
        self.chinese_percent_req = re.compile(rf"(?:负|零下)?百分之\s*{chinese_number}")
        self.arabic_number_req = re.compile(rf"[+-]?(?:{arabic_core}){scientific_suffix}")
        self.chinese_number_req = re.compile(chinese_number)
        self.datetime_req = re.compile(
            rf"(?:{token})\s*[-年./]\s*(?:{token})\s*[-月./]\s*(?:{token})\s*[日号]?"
        )
        self.time_req = re.compile(
            rf"(?:上午|早上|凌晨|中午|下午|晚上|傍晚)?\s*(?:{token})\s*"
            rf"(?:[:：]\s*(?:{token})(?:\s*[:：]\s*(?:{token}))?|"
            rf"[点时]\s*(?:{token})\s*分(?:\s*(?:{token})\s*秒)?)"
        )

    @staticmethod
    def _decimal_to_str(value: Decimal) -> str:
        if value == 0:
            return "0"
        if value == value.to_integral_value():
            return str(value.quantize(Decimal(1)))
        return format(value.normalize(), "f").rstrip("0").rstrip(".")

    @staticmethod
    def _span_overlaps(span: tuple[int, int], spans: list[tuple[int, int]]) -> bool:
        start, end = span
        return any(start < s_end and end > s_start for s_start, s_end in spans)

    @staticmethod
    def _strip_sign(value: str) -> tuple[str, int]:
        value = value.strip()
        if value.startswith(("负", "零下", "-")):
            if value.startswith("零下"):
                return value[2:].strip(), -1
            return value[1:].strip(), -1
        if value.startswith("+"):
            return value[1:].strip(), 1
        return value, 1

    @classmethod
    def _parse_chinese_integer(cls, value: str) -> int:
        if not value:
            return 0

        if not any(ch in value for ch in [*cls._CHINESE_UNITS, *cls._CHINESE_SECTION_UNITS]):
            return int("".join(str(cls._CHINESE_DIGITS[ch]) for ch in value))

        total = 0
        section = 0
        number = 0
        for ch in value:
            if ch in cls._CHINESE_DIGITS:
                number = cls._CHINESE_DIGITS[ch]
            elif ch in cls._CHINESE_UNITS:
                section += (number or 1) * cls._CHINESE_UNITS[ch]
                number = 0
            elif ch in cls._CHINESE_SECTION_UNITS:
                section = (section + number) * cls._CHINESE_SECTION_UNITS[ch]
                total += section
                section = 0
                number = 0

        return total + section + number

    @classmethod
    def _parse_chinese_decimal(cls, value: str) -> Decimal:
        value, sign = cls._strip_sign(value)
        integer_part, _, decimal_part = value.partition("点")
        number = Decimal(cls._parse_chinese_integer(integer_part))
        if decimal_part:
            decimal_digits = "".join(str(cls._CHINESE_DIGITS[ch]) for ch in decimal_part)
            number += Decimal(f"0.{decimal_digits}")
        return number * sign

    @classmethod
    def _parse_arabic_decimal(cls, value: str) -> Decimal:
        value = value.replace(" ", "").replace(",", "")
        scientific_match = re.search(
            r"^(.*?)(?:[×xX*]10\^?([+-]?\d+)|[eE]([+-]?\d+))$",
            value,
        )
        if scientific_match:
            base_text = scientific_match.group(1)
            exponent = int(scientific_match.group(2) or scientific_match.group(3))
            return Decimal(base_text) * (Decimal(10) ** exponent)
        return Decimal(value)

    @staticmethod
    def _looks_like_long_identifier(value: str) -> bool:
        digits = re.sub(r"\D", "", value)
        return len(digits) >= 8 and re.fullmatch(r"[+-]?[\d,]+", value.strip()) is not None

    @staticmethod
    def _looks_like_common_chinese_word(text: str, span: tuple[int, int]) -> bool:
        start, end = span
        value = text[start:end]
        if value == "百" and end < len(text) and text[end] == "分":
            return True
        if value in {"一", "二", "两", "三", "四", "五", "六", "七", "八", "九"}:
            next_char = text[end] if end < len(text) else ""
            return next_char in {"个", "些", "种", "名", "位"}
        return False

    def _skip_spans(self, text: str) -> list[tuple[int, int]]:
        spans = [match.span() for match in self.datetime_req.finditer(text)]
        spans.extend(match.span() for match in self.time_req.finditer(text))
        return spans

    def _append_result(
        self,
        results: list[dict[str, str | int]],
        consumed_spans: list[tuple[int, int]],
        match: re.Match,
        number: Decimal,
        precision: str,
        raw_text: str,
        unit: str = "",
        absolute: bool = False,
    ) -> None:
        start, end = match.span()
        if absolute:
            number = abs(number)
        results.append(
            {
                "number": self._decimal_to_str(number),
                "raw_text": raw_text,
                "unit": unit,
                "raw_context": raw_text,
                "precision": precision,
                "start": start,
            }
        )
        consumed_spans.append((start, end))

    def parse(self, text: str, absolute: bool = False) -> list[dict[str, str]]:
        if not text:
            return []

        normalized_text = text.translate(self._FULLWIDTH_TRANS)
        skip_spans = self._skip_spans(normalized_text)
        consumed_spans = list(skip_spans)
        results: list[dict[str, str | int]] = []

        for match in self.arabic_percent_req.finditer(normalized_text):
            if self._span_overlaps(match.span(), consumed_spans):
                continue
            raw_text = text[match.start() : match.end()]
            number_text = normalized_text[match.start() : match.end()].rstrip("%").strip()
            try:
                number = self._parse_arabic_decimal(number_text) / Decimal(100)
            except InvalidOperation:
                continue
            self._append_result(
                results,
                consumed_spans,
                match,
                number,
                "percent",
                raw_text,
                "%",
                absolute,
            )

        for match in self.chinese_percent_req.finditer(normalized_text):
            if self._span_overlaps(match.span(), consumed_spans):
                continue
            raw_text = text[match.start() : match.end()]
            percent_text = normalized_text[match.start() : match.end()]
            negative = -1 if percent_text.startswith(("负", "零下")) else 1
            number_text = re.sub(r"^(?:负|零下)?百分之\s*", "", percent_text)
            number = self._parse_chinese_decimal(number_text) * negative / Decimal(100)
            self._append_result(
                results,
                consumed_spans,
                match,
                number,
                "percent",
                raw_text,
                "%",
                absolute,
            )

        for match in self.arabic_number_req.finditer(normalized_text):
            if self._span_overlaps(match.span(), consumed_spans):
                continue
            raw_text = text[match.start() : match.end()]
            number_text = normalized_text[match.start() : match.end()]
            if self._looks_like_long_identifier(number_text):
                continue
            try:
                number = self._parse_arabic_decimal(number_text)
            except InvalidOperation:
                continue
            precision = "decimal" if "." in number_text else "integer"
            self._append_result(
                results,
                consumed_spans,
                match,
                number,
                precision,
                raw_text,
                absolute=absolute,
            )

        for match in self.chinese_number_req.finditer(normalized_text):
            if self._span_overlaps(match.span(), consumed_spans):
                continue
            raw_text = text[match.start() : match.end()]
            number_text = normalized_text[match.start() : match.end()]
            if self._looks_like_common_chinese_word(normalized_text, match.span()):
                continue
            number = self._parse_chinese_decimal(number_text)
            precision = "decimal" if "点" in number_text else "integer"
            self._append_result(
                results,
                consumed_spans,
                match,
                number,
                precision,
                raw_text,
                absolute=absolute,
            )

        results.sort(key=lambda item: int(item["start"]))
        return [
            {
                "number": str(item["number"]),
                "raw_text": str(item["raw_text"]),
                "unit": str(item["unit"]),
                "raw_context": str(item["raw_context"]),
                "precision": str(item["precision"]),
            }
            for item in results
        ]


__all__ = ["StrNumberParserCore"]
