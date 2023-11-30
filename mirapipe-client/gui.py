import ssl
from typing import Literal
from queue import Queue
from ttkbootstrap import Entry, Button, Text, Window, Label, LabelFrame
from pathlib import Path
import threading
import socket
from loguru import logger
from .types import ClientStateStore, ScanStatus
from .utils import validate_server_url, validate_port_range

Msg = tuple[str, Literal["pre", "scan", "result"]]
MsgQueue = Queue[Msg]


class ClientGUI:
    def __init__(self):
        self.root = Window(title="Mirapipe Client", themename="darkly", size=(800, 600))
        self.root.resizable(False, False)
        self.root.iconbitmap(Path(__file__).parent / "assets" / "logo.ico")
        self.state = ClientStateStore(port_range=(2000, 3000), server="localhost", scan_state=ScanStatus.NOT_SCANNED)
        self.msg_queue: MsgQueue = Queue()
        self._gui_init()
        self._component_init()
        self._text_color_init()
        self._message_update()

    def _gui_init(self):
        # 客户端界面布局
        ## 服务器选择区域
        url_check_func = self.root.register(validate_server_url)
        port_range_func = self.root.register(validate_port_range)
        self.scan_host_frame = LabelFrame(self.root, text="扫描地址", bootstyle="primary")  # type: ignore
        self.scan_host_frame.place(x=5, y=5, width=200, height=50)
        self.scan_host_entry = Entry(self.root, validate="focus", validatecommand=(url_check_func, "%P"))
        self.scan_host_entry.place(in_=self.scan_host_frame, x=5, y=0, width=185, height=25)
        ## 端口选择区域
        self.port_range_frame = LabelFrame(self.root, text="端口范围", bootstyle="info")  # type: ignore
        self.port_range_frame.place(x=210, y=5, width=200, height=50)
        self.port_range_entry = Entry(self.root, validate="focus", validatecommand=(port_range_func, "%P"))
        self.port_range_entry.place(in_=self.port_range_frame, x=5, y=0, width=185, height=25)
        ## 连接状态显示区域
        self.connect_status_frame = LabelFrame(self.root, text="连接状态", bootstyle="light")  # type: ignore
        self.connect_status_frame.place(x=415, y=5, width=100, height=50)
        self.connect_status = Label(self.root)
        self.connect_status.place(in_=self.connect_status_frame, x=10, y=0, width=80, height=25)
        ## 开始扫描按钮
        self.connect_button = Button(self.root, text="开始扫描", command=self.start_scan)
        self.connect_button.place(x=690, y=20, width=100, height=30)
        ## 消息显示区域
        self.message_frame = LabelFrame(self.root, text="结果显示", bootstyle="light")  # type: ignore
        self.message_frame.place(x=5, y=60, width=790, height=535)
        self.message_text = Text(self.root, state="disabled")
        self.message_text.place(in_=self.message_frame, x=5, y=0, width=778, height=510)

    def _component_init(self):
        # 服务器地址初始化
        self.scan_host_entry.insert(0, self.state["server"])
        # 端口范围初始化
        self.port_range_entry.insert(0, "2000-3000")
        # 连接状态初始化
        self.connect_status.configure(text=self.state["scan_state"], bootstyle="inverse-danger", anchor="center")  # type: ignore

    def _text_color_init(self):
        """初始化文本颜色"""
        self.message_text.tag_configure("pre", foreground="lightblue")
        self.message_text.tag_configure("scan", foreground="lightgreen")
        self.message_text.tag_configure("result", foreground="white")

    def display(self):
        """显示GUI"""
        self.root.mainloop()

    def start_scan(self):
        """连接服务器"""
        # 清空消息
        self.message_text.configure(state="normal")
        self.message_text.delete("1.0", "end")
        self.message_text.configure(state="disabled")
        # 开始扫描
        host = self.scan_host_entry.get()
        port_range_str = self.port_range_entry.get()
        port_list = [int(port) for port in port_range_str.split("-")]
        port_range = range(port_list[0], port_list[-1] + 1)
        logger.info(f"开始扫描{host}:{port_list}")
        self._message_record(f"开始扫描{host}:{port_list}\n", "pre")
        self.scan_result: dict[int, tuple[str,str]] = {}
        self.state["scan_state"] = ScanStatus.SCANNING
        self.connect_status.configure(text=self.state["scan_state"], bootstyle="inverse-warning")  # type: ignore
        self.root.after(10, self._scan, host, port_range)
        self.root.after(10, self._check_scan_finish)

    def _scan(self, host: str, port_range: range):
        threads = []
        for port in port_range:
            logger.debug(f"scan {port}")
            thread = threading.Thread(target=self._scan_port, args=(host, port))
            thread.start()
            threads.append(thread)

    def _scan_port(self, host: str, port: int):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex((host, port))
                if result == 0:
                    self.scan_result[port] = ("open", "common")
                else:
                    self.scan_result[port] = ("close", "common")
        except Exception as e:
            self.scan_result[port] = ("error", str(e))
        if self.scan_result[port][0] == "open":
            try:
                context = ssl.create_default_context()
                with socket.create_connection((host, port)) as sock:
                    with context.wrap_socket(sock, server_hostname=host) as ssock:
                        logger.debug(ssock.version())
                        self._message_record(f"{port} ssl version: {ssock.version()}\n", "scan")
                        self.scan_result[port] = ("ssl", ssock.version() or "unknown ver")
            except ssl.SSLError as e:
                self.scan_result[port] = ("maybe ssl", str(e))
            except OSError as e:
                self.scan_result[port] = ("error", str(e))

        log_msg = f"扫描{host}:{port}完成，结果为{self.scan_result[port]}\n"
        logger.info(log_msg)
        self._message_record(log_msg, "scan")

    def _check_scan_finish(self):
        """检查扫描是否完成"""
        threads = threading.enumerate()
        for thread in threads:
            if thread != threading.current_thread():
                self.root.after(100, self._check_scan_finish)
                return
        self.state["scan_state"] = ScanStatus.SCANNED
        self.connect_status.configure(text=self.state["scan_state"], bootstyle="inverse-success")  # type: ignore
        self._summary_scan_result()

    def _summary_scan_result(self):
        """汇总扫描结果"""
        open_ports: list[int] = []
        close_ports: list[int] = []
        ssl_ports: list[tuple[int, str]] = []
        maybe_ssl_ports: list[tuple[int, str]] = []
        error_ports: list[tuple[int, str]] = []
        unknows: list[tuple[int, tuple[str, str]]] = []
        for item in self.scan_result.items():
            match item:
                case port, ("open", "common"):
                    open_ports.append(port)
                case port, ("close", "common"):
                    close_ports.append(port)
                case port, ("ssl", version):
                    ssl_ports.append((port, version))
                case port, ("maybe ssl", msg):
                    maybe_ssl_ports.append((port, msg))
                case port, ("error", msg):
                    error_ports.append((port, msg))
                case _:
                    unknows.append(item)
        self._message_record(f"开放端口: {len(open_ports)}\n{open_ports or ""}\n", "result")
        self._message_record(f"关闭端口: {len(close_ports)}\n{close_ports or ""}\n", "result")
        self._message_record(f"SSL端口: {len(ssl_ports)}\n", "result")
        for port, version in ssl_ports:
            self._message_record(f"{port} ssl version: {version}\n", "result")
        self._message_record(f"可能是SSL端口: {len(maybe_ssl_ports)}\n", "result")
        for port, msg in maybe_ssl_ports:
            self._message_record(f"{port} {msg}\n", "result")
        self._message_record(f"错误端口: {len(error_ports)}\n", "result")
        for port, msg in error_ports:
            self._message_record(f"{port} {msg}\n", "result")
        self._message_record(f"未知端口: {len(unknows)}\n", "result")
        for port, msg in unknows:
            self._message_record(f"{port} {msg}\n", "result")
        self._message_record("扫描完成\n\n", "result")

    def _message_record(self, msg: str, tag: Literal["pre", "scan", "result"]):
        """记录消息"""
        logger.info(f"add to queue: {msg}")
        self.msg_queue.put((msg, tag))

    def _message_update(self):
        """记录消息"""
        while not self.msg_queue.empty():
            logger.debug("has msg")
            msg, tag = self.msg_queue.get()
            match tag:
                case "pre":
                    self.message_text.configure(state="normal")
                    self.message_text.insert("end", msg, tag)
                    self.message_text.configure(state="disabled")
                case "scan":
                    self.message_text.configure(state="normal")
                    self.message_text.insert("end", msg, tag)
                    self.message_text.configure(state="disabled")
                case "result":
                    self.message_text.configure(state="normal")
                    self.message_text.insert("end", msg, tag)
                    self.message_text.configure(state="disabled")
            self.message_text.see("end")
        self.root.after(10, self._message_update)
