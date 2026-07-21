from pathlib import Path

from fastapi import FastAPI
from fastapi.openapi.docs import get_swagger_ui_html


def configure_local_docs(
    app: FastAPI,
    *,
    static_dir: Path,
) -> None:
    """
    配置使用本地静态资源的 Swagger 文档页面。
    """

    if not static_dir.is_dir():
        raise RuntimeError(f"离线文档静态目录不存在: {static_dir}")

    @app.get("/docs", include_in_schema=False)
    async def custom_swagger_ui():
        """返回完全使用本地资源的 Swagger UI 页面。"""

        return get_swagger_ui_html(
            openapi_url=app.openapi_url,
            title=f"{app.title} - 离线文档",
            swagger_css_url="/static/docs/swagger-ui.css",
            swagger_js_url="/static/docs/swagger-ui-bundle.js",
            swagger_favicon_url="/static/docs/favicon.png",
        )


__all__ = ["configure_local_docs"]
