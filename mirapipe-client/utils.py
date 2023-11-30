import re

URL_PATTERN = re.compile(r"^(([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,6}|([0-9]{1,3}\.){3}[0-9]{1,3}|(localhost))$")

# 匹配类似 2000-3000（范围） 或者 2000（单个） 的端口范围
PORT_RANGE_PATTERN = re.compile(r"^([0-9]{1,5})-([0-9]{1,5})$|^([0-9]{1,5})$")

# 验证服务器地址
def validate_server_url(server_url: str):
    """验证服务器地址"""
    if not URL_PATTERN.match(server_url):
        return False
    return True

def validate_port_range(port_range: str):
    """验证端口范围"""
    if not PORT_RANGE_PATTERN.match(port_range):
        return False
    return True
