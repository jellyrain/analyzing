from analyzing.contracts.error import AnalyzingError


class ManifestValidationError(AnalyzingError):
    """
    插件 manifest 校验失败
    """


class CompatibilityError(AnalyzingError):
    """
    插件与宿主不兼容
    """


class PluginLoadError(AnalyzingError):
    """
    插件加载失败
    """


class PluginInvokeError(AnalyzingError):
    """
    插件调用失败
    """


__all__ = [
    "ManifestValidationError",
    "CompatibilityError",
    "PluginLoadError",
    "PluginInvokeError",
]
