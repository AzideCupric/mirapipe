import threading
from pathlib import Path
from loguru import logger
from . import start_server, create_server_context

cert_path = Path.cwd() / "certstore" / "server.pem"
ca_path = Path.cwd() / "certstore" / "ca.pem"

host = "localhost"
port = 5000

def start_server_thread():
    """启动服务器线程"""
    ctx = create_server_context(cert_path, "123456", ca_path)
    global server_thread
    server_thread = threading.Thread(target=start_server, args=(host, port, ctx))
    server_thread.daemon = True
    server_thread.start()
    logger.success("服务器线程启动")
    while True:
        pass

start_server_thread()
