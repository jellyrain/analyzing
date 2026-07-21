from analyzing.contracts.error import AnalyzingError


class MonitorError(AnalyzingError):
    """
    monitor 领域错误基类
    """


class MonitorTrackingError(MonitorError):
    """
    埋点记录失败
    """


class MonitorSchemaError(MonitorError):
    """
    monitor schema 初始化失败
    """


class MonitorQueryError(MonitorError):
    """
    monitor 查询失败
    """


__all__ = [
    "MonitorError",
    "MonitorQueryError",
    "MonitorSchemaError",
    "MonitorTrackingError",
]
