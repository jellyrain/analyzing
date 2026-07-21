from typing import Any

from fastapi.encoders import jsonable_encoder
from starlette.responses import JSONResponse


class APIResponse:
    """
    API响应封装类
    """

    @staticmethod
    def success(data: Any = None, message="成功") -> JSONResponse:
        """
        成功响应

        Args:
            data (Any, optional): 响应数据，默认为None
            message (str, optional): 响应消息，默认为"成功"

        Returns:
            JSONResponse: 成功响应对象
        """

        return APIResponse.success_code(200, data, message)

    @staticmethod
    def success_data_to_json(data: Any = None, message="成功") -> JSONResponse:
        """
        成功响应，数据转换为JSON可编码格式

        Args:
            data (Any, optional): 响应数据，默认为None
            message (str, optional): 响应消息，默认为"成功"

        Returns:
            JSONResponse: 成功响应对象
        """

        return APIResponse.success_code(200, jsonable_encoder(data), message)

    @staticmethod
    def success_code(code: int, data: Any = None, message="成功") -> JSONResponse:
        """
        成功响应

        Args:
            code (int): 响应状态码
            data (Any, optional): 响应数据，默认为None
            message (str, optional): 响应消息，默认为"成功"

        Returns:
            JSONResponse: 成功响应对象
        """

        return JSONResponse(
            status_code=code,
            content={"code": code, "message": message, "data": data},
        )

    @staticmethod
    def error(message: str = "内部服务器错误", data: Any = None) -> JSONResponse:
        """
        错误响应

        Args:
            message (str, optional): 错误消息，默认为"内部服务器错误"
            data (Any, optional): 响应数据，默认为None

        Returns:
            JSONResponse: 错误响应对象
        """

        return APIResponse.error_code(500, message, data)

    @staticmethod
    def error_data_to_json(
        message: str = "内部服务器错误", data: Any = None
    ) -> JSONResponse:
        """
        错误响应，数据转换为JSON可编码格式

        Args:
            message (str, optional): 错误消息，默认为"内部服务器错误"
            data (Any, optional): 响应数据，默认为None

        Returns:
            JSONResponse: 错误响应对象
        """

        return APIResponse.error_code(500, message, jsonable_encoder(data))

    @staticmethod
    def error_code(
        code: int, message: str = "内部服务器错误", data: Any = None
    ) -> JSONResponse:
        """
        错误响应

        Args:
            code (int): 响应状态码
            message (str, optional): 错误消息，默认为"内部服务器错误"
            data (Any, optional): 响应数据，默认为None

        Returns:
            JSONResponse: 错误响应对象
        """

        return JSONResponse(
            status_code=code,
            content={"code": code, "message": message, "data": data},
        )


__all__ = ["APIResponse"]
