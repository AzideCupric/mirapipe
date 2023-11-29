from typing import TypedDict
from enum import StrEnum

class ConnectStatus(StrEnum):
    """连接状态"""
    CONNECTED = "已连接"
    DISCONNECTED = "未连接"
    CONNECTING = "正在连接"

class ClientStateStore(TypedDict):
    """客户端数据状态存储"""
    cert_path: str
    server: str
    is_connected: ConnectStatus
