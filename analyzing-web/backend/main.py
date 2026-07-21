from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from src.api.lifespan import lifespan
from src.api.router import api_router

# Vite 构建产物目录，打包时随 Host 一起分发。
STATIC_DIR = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Analyzing APP", version="1.0.0", lifespan=lifespan)

app.include_router(api_router)

if STATIC_DIR.exists():
    app.mount(
        "/assets",
        StaticFiles(directory=STATIC_DIR / "assets"),
        name="assets",
    )

    @app.get("/{path:path}", include_in_schema=False)
    async def serve_spa(path: str, request: Request) -> FileResponse:
        # 优先返回真实静态文件，例如 favicon.ico。
        requested_file = (STATIC_DIR / path).resolve()

        if (
            path
            and requested_file.is_relative_to(STATIC_DIR)
            and requested_file.is_file()
        ):
            return FileResponse(requested_file)

        # React Router 的前端路由统一回退到 index.html。
        return FileResponse(STATIC_DIR / "index.html")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5304)
