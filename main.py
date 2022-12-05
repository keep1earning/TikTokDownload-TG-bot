import os

import json
import re
import requests
from retrying import retry
from telethon import TelegramClient, events
from tg_bot_config import api_hash, api_id
client = TelegramClient('tiktok', api_id, api_hash)


@retry(stop_max_attempt_number=3)
async def download(video_url, video_title, music_title, headers):
    # 视频下载
    if video_url == '':
        print('[  提示  ]:该视频可能无法下载哦~\r')
        return
    else:
        r = requests.get(url=video_url, headers=headers)
        if video_title == '':
            video_title = '[  提示  ]:此视频没有文案_%s\r' % music_title
        with open(f'{video_title}.mp4', 'wb') as f:
            f.write(r.content)
            print('[  视频  ]:%s下载完成\r' % video_title)
            return str(video_title)


async def video_download(url_arg):
    headers = {
        'user-agent': 'Mozilla/5.0 (Linux; Android 8.0; Pixel 2 Build/OPD3.170816.012) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/87.0.4280.88 Mobile Safari/537.36 Edg/87.0.664.66 '  # noqa
    }
    url = re.findall(r'https?://(?:[a-zA-Z]|\d|[$-_@.&+]|[!*,])+', url_arg)
    if len(url) > 0:
        url = url[0]
    else:
        return
    print(f"Downloading {url}")
    r = requests.get(url)
    key = re.findall(r'video/(\d+)?', str(r.url))[0]
    jx_url = f'https://www.iesdouyin.com/web/api/v2/aweme/iteminfo/?item_ids={key}'  # 官方接口
    js = json.loads(requests.get(url=jx_url, headers=headers).text)
    try:
        video_url = js['item_list'][0]['video']['play_addr']['url_list'][0]
        video_url = str(video_url).replace('playwm', 'play')  # 去水印后链接 # noqa
    except Exception as video_url_error:
        print(f'[  提示  ]:视频链接获取失败:{video_url_error}')
        return
    try:
        video_title = str(js['item_list'][0]['desc'])
        music_title = str(js['item_list'][0]['music']['author'])
    except Exception as title_error:
        print(f'[  提示  ]:标题获取失败{title_error}')
        return
    return await download(video_url, video_title, music_title, headers)


@client.on(events.NewMessage(pattern=r'https://v.douyin.com/(?i).*'))
async def my_event_handler(event):
    if 'douyin' in event.raw_text:
        f = await video_download(str(event.raw_text))
        if f is None:
            print("Error while downloading videos")
            return
        await event.delete()
        filename = str(f) + '.mp4'
        chat = await event.get_chat()
        await client.send_file(chat, filename)
        os.remove(filename)


client.start()
client.run_until_disconnected()
