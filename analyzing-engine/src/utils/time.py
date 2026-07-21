from datetime import datetime
from zoneinfo import ZoneInfo


def get_curr_time() -> datetime:
    return datetime.now(ZoneInfo("Asia/Shanghai"))


def get_curr_time_str() -> str:
    return datetime.now(ZoneInfo("Asia/Shanghai")).strftime("%Y-%m-%d %H:%M:%S")


__all__ = ["get_curr_time", "get_curr_time_str"]
