from typing import Literal
from tkinter import filedialog
from ttkbootstrap import Entry, Button, Text, Window, Label
from loguru import logger
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
from .types import ClientStateStore, ConnectStatus
from ..ssl import ssl_connect
from .utils import validate_server_url


class ClientGUI:
    def __init__(self):
        self.root = Window(title="Mirapipe Client", themename="darkly", size=(800, 600))
        self.root.resizable(False, False)
        self.root.iconbitmap(Path(__file__).parent.parent / "assets" / "logo.ico")
        self.state = ClientStateStore(
            cert_path=Path(), server=urlparse("https://localhost:5000"), is_connected=ConnectStatus.DISCONNECTED
        )
        self._gui_init()
        self._component_init()

    def _gui_init(self):
        # 客户端界面布局
        ## 证书选择区域
        self.cert_path_entry = Entry(self.root)
        self.cert_path_entry.place(x=5, y=10, width=200, height=30)
        self.select_cert_button = Button(
            self.root, text="选择证书", command=lambda: self.select_cert(self.cert_path_entry)
        )
        self.select_cert_button.place(x=200, y=10, width=100, height=30)
        ## 服务器连接区域
        url_check_func = self.root.register(validate_server_url)
        self.server_entry = Entry(self.root, validate="focus", validatecommand=(url_check_func, "%P"))
        self.server_entry.place(x=350, y=10, width=200, height=30)
        self.connect_button = Button(self.root, text="连接服务器", command=self.connect_to_server)
        self.connect_button.place(x=550, y=10, width=100, height=30)
        ## 连接状态显示区域
        self.connect_status = Label(self.root, text=self.state["is_connected"], style="inverse-danger")
        self.connect_status.place(x=700, y=15)
        ## 消息显示区域
        self.messages_text = Text(self.root, state="disabled")
        self.messages_text.place(x=5, y=50, width=790, height=500)
        ## 消息输入区域
        self.input_entry = Entry(self.root)
        self.input_entry.place(x=5, y=560, width=690, height=30)
        self.send_button = Button(self.root, text="发送", command=self.send_message)
        self.send_button.place(x=700, y=560, width=95, height=30)

    def _component_init(self):
        # 证书路径初始化
        self.cert_path_entry.insert(0, self.state["cert_path"].as_posix())
        # 服务器地址初始化
        self.server_entry.insert(0, self.state["server"].geturl())
        # 连接状态初始化
        self.connect_status.configure(text=self.state["is_connected"], bootstyle="inverse-danger")  # type: ignore

    def display(self):
        """显示GUI"""
        self.root.mainloop()

    def select_cert(self, entry):
        """选择证书文件"""
        logger.info("选择证书文件")
        selected = filedialog.askopenfilename(
            title="选择证书文件", filetypes=[("证书文件", "*.pem"), ("所有文件", "*.*")]
        )
        logger.info(selected)
        self.cert_path_entry.delete(0, "end")
        self.cert_path_entry.insert(0, selected)
        self.cert_path_entry.xview_moveto(1)
        self.state["cert_path"] = Path(selected)

    def connect_to_server(self):
        """连接服务器"""
        def update_connect_status(status: ConnectStatus, bootstyle: str = "inverse-danger"):
            self.state["is_connected"] = status
            self.connect_status.configure(text=self.state["is_connected"], bootstyle=bootstyle) # type: ignore
        self.root.after(10, update_connect_status, ConnectStatus.CONNECTING)

        self.state["server"] = urlparse(self.server_entry.get())
        logger.info(f"连接服务器:{self.state["server"]}")
        connectable= self.state["server"].netloc.split(":")
        if len(connectable) == 1:
            host, port = connectable[0], 443
        else:
            host, port = connectable

        if not self.state["cert_path"].exists():
            logger.warning("证书文件不存在")
            self._record_msg("证书文件不存在", "sys")
            self.root.after(10, update_connect_status, ConnectStatus.DISCONNECTED)
            return

        try:
            self.ssock = ssl_connect(host, int(port), self.state["cert_path"])
        except Exception as e:
            logger.error(f"连接失败： {e}")
            self._record_msg(f"连接失败: {e}", "sys")
            self.root.after(10, update_connect_status, ConnectStatus.DISCONNECTED)
            return

        try:
            self.ssock.sendall(b"Hello, World!")
            self.root.after(10, update_connect_status, ConnectStatus.CONNECTED, "inverse-success")
            logger.info("连接成功")
            self._record_msg("连接成功", "sys")
        except Exception as e:
            logger.error(f"连接失败:{e}")
            self._record_msg(f"连接失败:{e}", "sys")
            self.root.after(10, update_connect_status, ConnectStatus.DISCONNECTED)
        finally:
            self.ssock.close()

    def send_message(self):
        """发送消息"""
        message = self.input_entry.get()
        if self.state["is_connected"] != ConnectStatus.CONNECTED:
            logger.warning("未连接到服务器")
            self._record_msg("未连接到服务器", "sys")

        logger.info(f"发送消息:{message}")
        self._record_msg(message, "send")

    def _record_msg(self, message: str, type: Literal["sys", "send", "recv"]):
        """发送消息记录到聊天框并清除输入框"""
        now = datetime.now().strftime("%m-%d %H:%M:%S")
        tag = f"#{type}"
        match type:
            case "sys":
                msg = f"[系统消息] {now}:\n{message}\n"
                self._send_message_recorder(msg, tag)
            case "send":
                msg = f"[发送消息] {now}:\n{message}\n"
                self._send_message_recorder(msg, tag)
            case "recv":
                msg = f"[接收消息] {now}:\n{message}\n"
                self._send_message_recorder(msg, tag)

    def _send_message_recorder(self, message: str, m_tag: str):
        self.input_entry.delete(0, "end")
        self.messages_text.configure(state="normal")
        self.messages_text.insert("end", message, m_tag)
        self._set_msg_color(m_tag)
        self.messages_text.see("end")
        self.messages_text.configure(state="disabled")

    def _set_msg_color(self, tag: str):
        """设置消息颜色"""
        connect_state = self.state["is_connected"] == ConnectStatus.CONNECTED
        match tag:
            case "#sys":
                self.messages_text.tag_config(tag, foreground="red")
            case "#send":
                self.messages_text.tag_config(tag, foreground="green" if connect_state else "orange")
            case "#recv":
                self.messages_text.tag_config(tag, foreground="blue")
