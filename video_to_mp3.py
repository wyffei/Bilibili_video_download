# !/usr/bin/python
# -*- coding:utf-8 -*-
"""
批量将"书名文件夹"下所有子文件夹里的视频文件(.flv/.mp4/.mkv等)转换为 mp3,
转换后的 mp3 统一放在"书名"这一级总文件夹下(不再散落在各章节子文件夹里)。

目录结构示例(转换前):
    《枪炮、病菌与钢铁》/
    ├── 1 致我的中国读者/
    │   └── 1 致我的中国读者.flv
    ├── 2 前言、为什么说世界历史就像洋葱一样/
    │   └── 2 前言、为什么说世界历史就像洋葱一样.flv
    ...

转换后:
    《枪炮、病菌与钢铁》/
    ├── 1 致我的中国读者/
    │   └── 1 致我的中国读者.flv
    ├── 1 致我的中国读者.mp3          <- 新生成,和视频同名,但在总文件夹这一级
    ├── 2 前言、为什么说世界历史就像洋葱一样/
    │   └── ...flv
    ├── 2 前言、为什么说世界历史就像洋葱一样.mp3
    ...

用法:
    python video_to_mp3.py "F:\文件\Bilibili_video_download-master\Bilibili_video_download-master\bilibili_video\《枪炮、病菌与钢铁》"
    不带参数运行则默认处理脚本所在目录下的 bilibili_video 文件夹

依赖: 系统需要能在命令行直接调用 ffmpeg (即 `ffmpeg -version` 能正常输出)
"""

import os
import sys
import subprocess

# 支持转换的视频后缀
VIDEO_EXTS = ('.flv', '.mp4', '.mkv', '.avi', '.mov')


def check_ffmpeg():
    """检查 ffmpeg 是否可以在命令行直接调用"""
    try:
        subprocess.run(
            ['ffmpeg', '-version'],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def get_output_name(video_path, book_folder):
    """
    决定输出的 mp3 文件名(不含路径):
    - 如果视频直接在总文件夹(book_folder)下, 用视频自己的文件名
    - 如果视频在某个子文件夹(章节)里, 用"子文件夹名"作为 mp3 文件名
      (子文件夹通常就是章节标题,比视频自身文件名更可靠、更不容易重名)
    """
    parent_dir = os.path.dirname(video_path)
    if os.path.normpath(parent_dir) == os.path.normpath(book_folder):
        # 视频直接放在总文件夹下, 没有子文件夹
        name, _ext = os.path.splitext(os.path.basename(video_path))
        return name
    else:
        # 用视频所在的直接父文件夹名作为 mp3 文件名
        return os.path.basename(parent_dir)


def convert_to_mp3(video_path, mp3_path, overwrite=False):
    """把单个视频文件转换为指定路径的 mp3"""
    if os.path.exists(mp3_path) and not overwrite:
        print(f'[跳过,已存在]: {mp3_path}')
        return

    print(f'[转换中]: {video_path} -> {mp3_path}')
    cmd = [
        'ffmpeg',
        '-y' if overwrite else '-n',
        '-i', video_path,
        '-vn',                    # 不要视频流
        '-acodec', 'libmp3lame',  # mp3 编码
        '-q:a', '2',              # 音质等级, 0(最好)-9(最差), 2约等于190kbps
        mp3_path
    ]
    result = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    if result.returncode == 0:
        print(f'[完成]: {mp3_path}')
    else:
        print(f'[失败]: {video_path}')
        print(result.stderr.decode(errors='ignore'))


def find_video_files(folder):
    """递归查找文件夹内所有支持的视频文件"""
    video_files = []
    for root, _dirs, files in os.walk(folder):
        for name in files:
            if name.lower().endswith(VIDEO_EXTS):
                video_files.append(os.path.join(root, name))
    return video_files


def main():
    if not check_ffmpeg():
        print('[错误] 找不到 ffmpeg,请确认已安装并加入 PATH,或已在当前虚拟环境中可用')
        sys.exit(1)

    # 目标文件夹(书名这一级): 命令行参数优先, 否则用脚本同级目录下的 bilibili_video
    if len(sys.argv) > 1:
        folder = sys.argv[1]
    else:
        folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'bilibili_video')

    if not os.path.isdir(folder):
        print(f'[错误] 找不到文件夹: {folder}')
        sys.exit(1)

    video_files = find_video_files(folder)
    if not video_files:
        print(f'[提示] 在 {folder} 中没有找到可转换的视频文件')
        return

    print(f'[共找到 {len(video_files)} 个视频文件, mp3 将统一输出到]: {folder}\n')

    used_names = {}  # 防止重名互相覆盖
    for video_path in video_files:
        name = get_output_name(video_path, folder)
        # 如果出现重名(极少见), 自动加序号区分
        if name in used_names:
            used_names[name] += 1
            name = f'{name}_{used_names[name]}'
        else:
            used_names[name] = 0

        mp3_path = os.path.join(folder, name + '.mp3')
        convert_to_mp3(video_path, mp3_path)

    print('\n[全部处理完成]')


if __name__ == '__main__':
    main()