import re

URL_PATTERN = re.compile(r"^(http|https)://[a-zA-Z0-9\-\.]+(:[0-9]+)?/?$")

# 验证服务器地址
def validate_server_url(server_url: str):
    """验证服务器地址"""
    if not URL_PATTERN.match(server_url):
        return False
    return True
