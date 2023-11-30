import ssl
import socket
from pathlib import Path

ca_path = Path.cwd() / "certstore" / "ca.pem"

def ssl_connect(host: str, port: int, cert_path: Path):
    context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH, cafile=ca_path)
    context.load_cert_chain(cert_path, password="123456") # 如果证书和私钥在同一个文件中，可以省略第二个参数
    context.load_verify_locations(ca_path)
    with socket.create_connection((host, port)) as sock:
        with context.wrap_socket(sock, server_hostname=host) as ssock:
            return ssock
