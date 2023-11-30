import ssl
import socket
from pathlib import Path
from loguru import logger

def create_server_context(cert_path: Path, password: str, ca_path: Path):
    """创建服务器上下文"""
    context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH, cafile=ca_path)
    context.load_cert_chain(cert_path, password=password)
    context.load_verify_locations(ca_path)
    context.verify_mode = ssl.CERT_REQUIRED # 要求客户端提供证书
    return context

def start_server(host: str, port: int, context: ssl.SSLContext):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM, 0) as sock:
        sock.bind((host, port))
        sock.listen(5)
        with context.wrap_socket(sock, server_side=True) as ssock:
            while True:
                conn, addr = ssock.accept()
                logger.info(f"Connected by {addr}")
                handle_client(conn, addr)

def handle_client(conn: socket.socket, addr):
    with conn:
        while True:
            data = conn.recv(1024)
            if not data:
                break
            update_message(data.decode("utf-8"))
            respond_recv(conn)

def update_message(message: str):
    """更新消息"""
    logger.info(f"接收到消息:{message}")

def respond_recv(conn: socket.socket):
    """响应接收"""
    conn.sendall(b"Message received")
