import os
import asyncio
from fastapi import FastAPI
from pydantic import BaseModel
from slack_sdk.web.async_client import AsyncWebClient
from slack_sdk.errors import SlackApiError
from wxpy import Bot, Group, TEXT

# 初始化 FastAPI
app = FastAPI()

# 初始化 Slack 客户端
SLACK_API_TOKEN = os.getenv('SLACK_API_TOKEN')
slack_client = AsyncWebClient(token=SLACK_API_TOKEN)

# 初始化微信机器人
wechat_bot = Bot()

# 在这里设置你的微信群名称
GROUP_NAME = 'Your Group Name'
group = wechat_bot.groups().search(GROUP_NAME)[0]

class Message(BaseModel):
    text: str

@app.post('/send_message_to_slack')
async def send_message_to_slack(message: Message):
    try:
        response = await slack_client.chat_postMessage(channel='#general', text=message.text)
        return {'status': 'success'}
    except SlackApiError as e:
        return {'status': 'error', 'error': str(e)}

@app.post('/send_message_to_wechat')
async def send_message_to_wechat(message: Message):
    group.send(message.text)
    return {'status': 'success'}

# 监听微信群消息并发送到 Slack
@wechat_bot.register(Group, TEXT)
def forward_message_to_slack(msg):
    if msg.chat == group:
        asyncio.run(send_message_to_slack(Message(text=msg.text)))

# 从 Slack 接收消息并发送到微信群
async def listen_to_slack_messages():
    while True:
        try:
            response = await slack_client.conversations_history(channel='#general', limit=1)
            message = response['messages'][0]['text']
            await send_message_to_wechat(Message(text=message))
        except (SlackApiError, KeyError) as e:
            print(f"Error: {e}")
        await asyncio.sleep(5)

# 开始监听 Slack 消息
asyncio.run(listen_to_slack_messages())
