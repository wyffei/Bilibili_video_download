# !/usr/bin/python
# -*- coding:utf-8 -*-
# time: 2019/04/17--08:12
__author__ = 'Henry'


'''
项目: B站视频下载

版本1: 加密API版,不需要加入cookie,直接即可下载1080p视频

20190422 - 增加多P视频单独下载其中一集的功能
'''
import imageio
# imageio.plugins.ffmpeg.download()

import requests, time, hashlib, urllib.request, re, json
from moviepy.editor import *
import os, sys


# 访问API地址
def get_play_list(bvid, cid, quality, start_url):
    headers = {
        'Referer': start_url,
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    url_api = 'https://api.bilibili.com/x/player/playurl?bvid=%s&cid=%s&qn=%s&fnval=0&fnver=0&fourk=1' % (bvid, cid, quality)
    html = requests.get(url_api, headers=headers).json()
    if html.get('code') != 0:
        print('[获取视频地址失败]:', html.get('message'))
        return []
    video_list = [i['url'] for i in html['data']['durl']]
    return video_list


# 下载视频
'''
 urllib.urlretrieve 的回调函数：
def callbackfunc(blocknum, blocksize, totalsize):
    @blocknum:  已经下载的数据块
    @blocksize: 数据块的大小
    @totalsize: 远程文件的大小
'''


def Schedule_cmd(blocknum, blocksize, totalsize):
    speed = (blocknum * blocksize) / (time.time() - start_time)
    # speed_str = " Speed: %.2f" % speed
    speed_str = " Speed: %s" % format_size(speed)
    recv_size = blocknum * blocksize

    # 设置下载进度条
    f = sys.stdout
    pervent = recv_size / totalsize
    percent_str = "%.2f%%" % (pervent * 100)
    n = round(pervent * 50)
    s = ('#' * n).ljust(50, '-')
    f.write(percent_str.ljust(8, ' ') + '[' + s + ']' + speed_str)
    f.flush()
    # time.sleep(0.1)
    f.write('\r')


def Schedule(blocknum, blocksize, totalsize):
    speed = (blocknum * blocksize) / (time.time() - start_time)
    # speed_str = " Speed: %.2f" % speed
    speed_str = " Speed: %s" % format_size(speed)
    recv_size = blocknum * blocksize

    # 设置下载进度条
    f = sys.stdout
    pervent = recv_size / totalsize
    percent_str = "%.2f%%" % (pervent * 100)
    n = round(pervent * 50)
    s = ('#' * n).ljust(50, '-')
    print(percent_str.ljust(6, ' ') + '-' + speed_str)
    f.flush()
    time.sleep(2)
    # print('\r')


# 字节bytes转化K\M\G
def format_size(bytes):
    try:
        bytes = float(bytes)
        kb = bytes / 1024
    except:
        print("传入的字节格式不对")
        return "Error"
    if kb >= 1024:
        M = kb / 1024
        if M >= 1024:
            G = M / 1024
            return "%.3fG" % (G)
        else:
            return "%.3fM" % (M)
    else:
        return "%.3fK" % (kb)


#  下载视频
def down_video(video_list, title, start_url, page):
    num = 1
    print('[正在下载P{}段视频,请稍等...]:'.format(page) + title)
    currentVideoPath = os.path.join(sys.path[0], 'bilibili_video', title)  # 当前目录作为下载目录
    for i in video_list:
        opener = urllib.request.build_opener()
        # 请求头
        opener.addheaders = [
            # ('Host', 'upos-hz-mirrorks3.acgvideo.com'),  #注意修改host,不用也行
            ('User-Agent', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.13; rv:56.0) Gecko/20100101 Firefox/56.0'),
            ('Accept', '*/*'),
            ('Accept-Language', 'en-US,en;q=0.5'),
            ('Accept-Encoding', 'gzip, deflate, br'),
            ('Range', 'bytes=0-'),  # Range 的值要为 bytes=0- 才能下载完整视频
            ('Referer', start_url),  # 注意修改referer,必须要加的!
            ('Origin', 'https://www.bilibili.com'),
            ('Connection', 'keep-alive'),
        ]
        urllib.request.install_opener(opener)
        # 创建文件夹存放下载的视频
        if not os.path.exists(currentVideoPath):
            os.makedirs(currentVideoPath)
        # 开始下载
        if len(video_list) > 1:
            urllib.request.urlretrieve(url=i, filename=os.path.join(currentVideoPath, r'{}-{}.flv'.format(title, num)),reporthook=Schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'
        else:
            urllib.request.urlretrieve(url=i, filename=os.path.join(currentVideoPath, r'{}.flv'.format(title)),reporthook=Schedule_cmd)  # 写成mp4也行  title + '-' + num + '.flv'
        num += 1

# 合并视频
def combine_video(video_list, title):
    currentVideoPath = os.path.join(sys.path[0], 'bilibili_video', title)  # 当前目录作为下载目录
    if not os.path.exists(currentVideoPath):
        os.makedirs(currentVideoPath)
    if len(video_list) >= 2:
        # 视频大于一段才要合并
        print('[下载完成,正在合并视频...]:' + title)
        # 定义一个数组
        L = []
        # 访问 video 文件夹 (假设视频都放在这里面)
        root_dir = currentVideoPath
        # 遍历所有文件
        for file in sorted(os.listdir(root_dir), key=lambda x: int(x[x.rindex("-") + 1:x.rindex(".")])):
            # 如果后缀名为 .mp4/.flv
            if os.path.splitext(file)[1] == '.flv':
                # 拼接成完整路径
                filePath = os.path.join(root_dir, file)
                # 载入视频
                video = VideoFileClip(filePath)
                # 添加到数组
                L.append(video)
        # 拼接视频
        final_clip = concatenate_videoclips(L)
        # 生成目标视频文件
        final_clip.to_videofile(os.path.join(root_dir, r'{}.mp4'.format(title)), fps=24, remove_temp=False)
        print('[视频合并完成]' + title)

    else:
        # 视频只有一段则直接打印下载完成
        print('[视频合并完成]:' + title)


if __name__ == '__main__':
    # 用户输入av号或者视频链接地址
    print('*' * 30 + 'B站视频下载小助手' + '*' * 30)
    start = input('请输入您要下载的B站av号或者视频链接地址:')
    if start.isdigit():  # 纯数字，当作av号
        start_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + start
    else:
        bv_match = re.search(r'(BV[0-9A-Za-z]{10})', start)
        av_match = re.search(r'/av(\d+)', start)
        if bv_match:  # 输入的是BV号或含BV号的链接
            start_url = 'https://api.bilibili.com/x/web-interface/view?bvid=' + bv_match.group(1)
        elif av_match:  # 输入的是av号或含av号的链接
            start_url = 'https://api.bilibili.com/x/web-interface/view?aid=' + av_match.group(1)
        else:
            print('无法识别输入的av号/BV号/视频链接，请重新检查后再试')
            exit()

    # 视频质量
    # <accept_format><![CDATA[flv,flv720,flv480,flv360]]></accept_format>
    # <accept_description><![CDATA[高清 1080P,高清 720P,清晰 480P,流畅 360P]]></accept_description>
    # <accept_quality><![CDATA[80,64,32,16]]></accept_quality>
    quality = input('请输入您要下载视频的清晰度(1080p:80;720p:64;480p:32;360p:16)(填写80或64或32或16):')
    # 获取视频的cid,title
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36'
    }
    html = requests.get(start_url, headers=headers).json()
    data = html['data']
    bvid = data['bvid']
    video_title=data["title"].replace(" ","_")
    cid_list = []
    if 'ugc_season' in data and data['ugc_season']:
        # 是合集(选集)视频,遍历所有分集
        episodes = []
        for section in data['ugc_season']['sections']:
            episodes.extend(section['episodes'])
        print(f'[检测到合集,共 {len(episodes)} 集]')
        cid_list = episodes  # 后面统一处理,字段名和pages略有不同,见下方for循环调整
    elif '?p=' in start:
        p = re.search(r'\?p=(\d+)', start).group(1)
        cid_list = [data['pages'][int(p) - 1]]
    else:
        cid_list = data['pages']
    for item in cid_list:
        if 'ugc_season' in data and data['ugc_season']:
            # 合集视频: 每一集用自己的 bvid
            cid = str(item['cid'])
            title = item['title']
            page = '1'
            video_url = 'https://www.bilibili.com/video/' + item['bvid'] + '/'
        else:
            cid = str(item['cid'])
            title = item['part'] or video_title
            page = str(item['page'])
            video_url = start_url + "/?p=" + page

        title = re.sub(r'[\/\\:*?"<>|]', '', title)
        print('[下载视频的cid]:' + cid)
        print('[下载视频的标题]:' + title)
        video_list = get_play_list(item.get('bvid', bvid), cid, quality, video_url)
        start_time = time.time()
        down_video(video_list, title, video_url, page)
        combine_video(video_list, title)

    # 如果是windows系统，下载完成后打开下载目录
    currentVideoPath = os.path.join(sys.path[0], 'bilibili_video')  # 当前目录作为下载目录
    if (sys.platform.startswith('win')):
        os.startfile(currentVideoPath)


# 分P视频下载测试: https://www.bilibili.com/video/av19516333/
