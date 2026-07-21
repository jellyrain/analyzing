import json
from typing import Any, Mapping, TextIO, TypeVar

from analyzing.runtime.errors import RuntimeProtocolError
from analyzing.contracts.model import AnalyzingModel

T = TypeVar("T", bound=AnalyzingModel)


def read_json_message(reader: TextIO) -> dict[str, Any] | None:
    """
    从文本流中读取一条 JSON 消息

    当前约定：
    - 一行就是一条消息
    - 空行会被自动跳过
    """

    while True:
        line = reader.readline()
        if line == "":
            raise EOFError("stdio 通道已关闭")

        stripped = line.strip()
        if not stripped:
            continue

        try:
            payload = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise RuntimeProtocolError("收到的消息不是合法 JSON") from exc

        if not isinstance(payload, dict):
            raise RuntimeProtocolError("收到的 JSON 消息必须是对象类型")

        return payload


def write_json_message(
    writer: TextIO,
    payload: Mapping[str, Any],
) -> None:
    """
    向文本流写入一条 JSON 消息
    """

    writer.write(
        json.dumps(
            dict(payload),
            ensure_ascii=True,
        )
    )
    writer.write("\n")
    writer.flush()


def read_model_message(
    reader: TextIO,
    model_type: type[T],
) -> T:
    """
    从文本流中读取一条消息并解析为模型
    """

    payload = read_json_message(reader)

    try:
        return model_type.model_validate(payload)
    except Exception as exc:
        raise RuntimeProtocolError(
            f"消息无法解析为模型: {model_type.__name__}"
        ) from exc


def write_model_message(
    writer: TextIO,
    model: AnalyzingModel,
) -> None:
    """
    将模型写入文本流
    """

    write_json_message(
        writer=writer,
        payload=model.model_dump(mode="json"),
    )


__all__ = [
    "read_json_message",
    "write_json_message",
    "read_model_message",
    "write_model_message",
]
