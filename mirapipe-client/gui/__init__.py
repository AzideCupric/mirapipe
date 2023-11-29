from tkinter import filedialog
from ttkbootstrap import Entry, Button, Text, Window, Label
from loguru import logger
from pathlib import Path

from .types import ClientStateStore, ConnectStatus

class ClientGUI:
    def __init__(self):
        self.root = Window(title="Mirapipe Client", themename="darkly", size=(800, 600))
        self.root.resizable(False, False)
        self.root.iconbitmap(Path(__file__).parent.parent / "assets" / "logo.ico")
        self.state = ClientStateStore(
            cert_path="",
            server="https://localhost:5000",
            is_connected=ConnectStatus.DISCONNECTED
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
        self.server_entry = Entry(self.root)
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
        self.cert_path_entry.insert(0, self.state["cert_path"])
        # 服务器地址初始化
        self.server_entry.insert(0, self.state["server"])
        # 连接状态初始化
        self.connect_status.configure(text=self.state["is_connected"], bootstyle="inverse-danger") #type: ignore

    def display(self):
        """显示GUI"""
        self.root.mainloop()

    def select_cert(self, entry):
        """选择证书文件"""
        logger.info("选择证书文件")
        selected = filedialog.askopenfilename()
        logger.info(selected)

    def connect_to_server(self):
        """连接服务器"""
        logger.info("连接服务器")
        self.state["is_connected"] = ConnectStatus.CONNECTING
        self.connect_status.configure(text=self.state["is_connected"], bootstyle="inverse-warning") #type: ignore

    def send_message(self):
        """发送消息"""
        logger.info("发送消息")

if __name__ == "__main__":
    gui = ClientGUI()
    gui.display()
