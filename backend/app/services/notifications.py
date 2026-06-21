from __future__ import annotations

import os
from datetime import datetime
import sys


def send_failure_notification(job_name: str, error_message: str) -> None:
    # 1. Log to system stderr
    print(
        f"[FAILURE WARNING] Job '{job_name}' failed at {datetime.now().isoformat()}: {error_message}",
        file=sys.stderr
    )

    # 2. Check if a webhook is configured in the environment
    webhook_url = os.getenv("NOTIFICATION_WEBHOOK")
    if not webhook_url:
        return

    try:
        import httpx

        # Format message content based on the chat application platform detected in the webhook URL
        if "open.feishu.cn" in webhook_url:
            # Feishu (Lark) Text message
            payload = {
                "msg_type": "text",
                "content": {
                    "text": f"⚠️ A-Quant Insight 任务运行失败通知\n\n【任务名称】: {job_name}\n【失败时间】: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n【错误详情】: {error_message}"
                }
            }
        elif "oapi.dingtalk.com" in webhook_url:
            # DingTalk Markdown message
            payload = {
                "msgtype": "markdown",
                "markdown": {
                    "title": "A-Quant 任务失败告警",
                    "text": f"### ⚠️ A-Quant Insight 任务运行失败\n\n**任务名称**: {job_name}\n\n**失败时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n**错误详情**: {error_message}"
                }
            }
        elif "qyapi.weixin.qq.com" in webhook_url:
            # WeChat Work Text message
            payload = {
                "msgtype": "text",
                "text": {
                    "content": f"⚠️ A-Quant Insight 任务运行失败\n任务名称: {job_name}\n失败时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n错误详情: {error_message}"
                }
            }
        else:
            # Standard custom json webhook payload
            payload = {
                "event": "job_failed",
                "job_name": job_name,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
                "text": f"⚠️ A-Quant Insight 任务 '{job_name}' 运行失败：{error_message}"
            }

        # Send HTTP POST synchronously (safe inside asynccontextmanager lifespan threads/schedulers)
        with httpx.Client(timeout=5.0) as client:
            client.post(webhook_url, json=payload)

    except Exception as e:
        print(f"Failed to send webhook failure notification: {e}", file=sys.stderr)
