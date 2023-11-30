from typing import TypedDict
from enum import StrEnum

class ScanStatus(StrEnum):
    """连接状态"""
    SCANNING = "正在扫描"
    SCANNED = "扫描完成"
    NOT_SCANNED = "未扫描"

class ClientStateStore(TypedDict):
    """客户端数据状态存储"""
    port_range: tuple[int, int]
    server: str
    scan_state: ScanStatus

