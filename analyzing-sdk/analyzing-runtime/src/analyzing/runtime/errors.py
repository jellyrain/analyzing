from analyzing.contracts.error import AnalyzingError


class RuntimeLoadError(AnalyzingError):
    """
    运行时加载失败
    """


class RuntimeInvokeError(AnalyzingError):
    """
    运行时调用失败
    """


class RuntimeProtocolError(AnalyzingError):
    """
    运行时通信失败
    """


__all__ = ["RuntimeLoadError", "RuntimeInvokeError", "RuntimeProtocolError"]
