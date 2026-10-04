"""ابزار سفارشی پروژه — توسط ACA ساخته شده."""
from __future__ import annotations

from typing import Any

from agent.options import AgentOptions
from agent.tool_impl import tool_result


def run(arguments: dict[str, Any], options: AgentOptions) -> str:
    import paramiko

    host = '109.122.249.130'
    username = 'root'
    password = '135101220'

    try:
        # ایجاد اتصال SSH
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(host, username=username, password=password)

        # اجرای دستور برای دریافت تنظیمات انجینکس
        stdin, stdout, stderr = client.exec_command('cat /etc/nginx/nginx.conf')
        nginx_config = stdout.read().decode('utf-8')

        client.close()
        return tool_result(True, nginx_config)
    except Exception as e:
        return tool_result(False, str(e))
