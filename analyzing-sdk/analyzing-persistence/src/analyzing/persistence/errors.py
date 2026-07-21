from analyzing.contracts.error import AnalyzingError


class PersistenceError(AnalyzingError):
    """
    persistence 领域错误基类
    """


class PersistenceWriteError(PersistenceError):
    """
    写入失败
    """


class PersistenceQueryError(PersistenceError):
    """
    查询失败
    """


class PersistenceUpdateError(PersistenceError):
    """
    更新失败
    """


class PersistenceDeleteError(PersistenceError):
    """
    删除失败
    """


class PersistenceProtocolError(PersistenceError):
    """
    sidecar/subprocess 协议错误
    """


__all__ = [
    "PersistenceDeleteError",
    "PersistenceError",
    "PersistenceProtocolError",
    "PersistenceQueryError",
    "PersistenceUpdateError",
    "PersistenceWriteError",
]