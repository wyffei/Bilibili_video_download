
## :dolphin:介绍
### 该项目为[Bilibili(b站)](https://www.bilibili.com/)视频下载。
****
## :dolphin:声明
### 软件均仅用于学习交流，请勿用于任何商业用途！感谢大家！

## :dolphin:爬虫版本
> **以下版本均为命令行交互式脚本:直接运行,不需要带任何命令行参数,运行后按提示依次输入即可**

- **版本一: bilibili_video_download_v1.py**
  > **加密API版,不需要加入cookie,直接即可下载1080p视频<br>**
  > **支持传入av号/BV号/视频链接,支持合集(选集)视频批量下载<br>**
  - 运行命令:
    ```
    python bilibili_video_download_v1.py
    ```
  - 运行后依次输入:
    | 提示 | 说明 |
    |---|---|
    | B站av号/BV号/视频链接地址 | 纯数字按av号处理;<br>也可直接粘贴含BV号/av号的完整视频链接;<br>多P视频链接末尾带`?p=2`则只下载第2集,不带则下载全部分P;<br>合集(选集)视频会自动识别并下载全部分集 |
    | 视频清晰度 | 填 `80`(1080P) / `64`(720P) / `32`(480P) / `16`(360P) |
  - 输出位置: 脚本所在目录下 `bilibili_video/<视频标题>/`,多P/多集会自动合并为一个 `.mp4`

- **版本二: bilibili_video_download_v2.py**
  > **1.无加密API版,但是需要加入登录后cookie中的SESSDATA字段,才可下载720p及以上视频**<br>
  > **2.如果想下载1080p+视频,需要带入B站大会员的cookie中的SESSDATA才行,普通用户的SESSDATA最多只能下载1080p视频；请定期更换代码第35行cookie中的SESSDATA值。跟换方法为：浏览器登录B站，在开发者模式(按F12) --> application --> cookie中找到SESSDATA值替换即可，一个月的有效期**
  - 运行命令:
    ```
    python bilibili_video_download_v2.py
    ```
  - 运行后依次输入:
    | 提示 | 说明 |
    |---|---|
    | av号或视频链接地址 | 仅支持纯数字av号,或含 `/av数字` 的完整链接;<br>**不支持BV号,也不支持合集(选集)视频**(如需这两项请用版本一) |
    | 视频清晰度 | 填 `116`(1080p60) / `112`(1080p+) / `80`(1080p) / `74`(720p60) / `64`(720p) / `32`(480p) / `16`(360p);<br>其中 `116`/`112`/`74`/`64` 都需要代码里的SESSDATA是大会员的,否则会被自动降级到最低清晰度 |
  - 输出位置: 同版本一,`bilibili_video/<视频标题>/`

- **版本三: bilibili_video_download_v3.py**(Windows) / **bilibili_video_download_v3-linux.py**(Linux)
  > **即版本二的升级版,为Threading多线程下载版本,下载速度大幅提升!**<br>
  - 运行命令:
    ```
    python bilibili_video_download_v3.py
    ```
    Linux下运行 `bilibili_video_download_v3-linux.py`,用法相同
  - 运行后依次输入:
    | 提示 | 说明 |
    |---|---|
    | av号或视频链接地址 | 仅支持纯数字av号,或含 `/av数字` 的完整链接;<br>**不支持BV号,也不支持合集(选集)视频**(如需这两项请用版本一) |
    | 视频清晰度 | 填 `80`(1080P) / `64`(720P) / `32`(480P) / `16`(360P) |
  - 输出位置: 同版本一,`bilibili_video/<视频标题>/`

- **版本四: GUI版本 - bilibili_video_download-GUI.py**
  > **在版本三基础上加入图形界面,操作更加友好<br>**
  - 运行命令:
    ```
    python bilibili_video_download-GUI.py
    ```
  - 运行后会弹出图形窗口,在界面输入框中填入av号/视频链接和清晰度,点击下载按钮即可,无需在命令行输入
  - 输出位置: 同版本一,`bilibili_video/<视频标题>/`

- **版本五: bilibili_video_download_bangumi.py**
  > **在版本一,三基础上增加下载B站番剧视频(eg: https://www.bilibili.com/bangumi/play/ep269835)<br>**
  - 运行命令:
    ```
    python bilibili_video_download_bangumi.py
    ```
  - 运行后依次输入:
    | 提示 | 说明 |
    |---|---|
    | 番剧完整链接地址 | 例如 `https://www.bilibili.com/bangumi/play/ep267692` |
    | 下载范围 | 填 `1`只下载当前这一集,或 `2`下载整部番剧的全集 |
    | 视频清晰度 | 填 `116`/`112`/`80`/`74`/`64`/`32`/`16` |
  - 输出位置: 同版本一,`bilibili_video/<番剧标题>/`

## :dolphin:音频处理工具
> **配合视频下载,适合处理有声书/听书类内容:下载视频 → 转换为mp3 → 按章节自动切分**

- **video_to_mp3.py**
  > **批量将`bilibili_video`下某个书名文件夹里所有子文件夹中的视频文件(.flv/.mp4/.mkv/.avi/.mov)转换为mp3,转换后的mp3统一放在书名这一级总文件夹下(不再散落在各章节子文件夹里)**<br>
  > **依赖: 系统需要能在命令行直接调用ffmpeg(即`ffmpeg -version`能正常输出)**<br>
  - 运行命令:
    ```
    python video_to_mp3.py "bilibili_video/《书名》"
    ```
  - 参数说明:
    | 参数 | 是否必填 | 说明 |
    |---|---|---|
    | 书名文件夹路径(位置参数) | ❌ | 不传时默认处理脚本同级目录下的 `bilibili_video` 整个文件夹 |
  - 输出位置: 转换后的mp3直接放在传入的"书名"文件夹这一级(不进入子文件夹);如果视频在某个章节子文件夹里,mp3文件名取该子文件夹名(通常就是章节标题);如果视频直接放在书名文件夹下,则用视频原文件名

- **split_mp3_by_chapter.py**
  > **基于语音识别(faster-whisper),自动检测音频里说出的"第一章""第二章"等文字标记,把一整段长mp3按章节切分成多段;每段如果超过指定大小,会再按时长自动拆分为更小的分段(避免单个文件过大,方便上传/分享)**<br>
  - 依赖安装:
    ```
    pip install faster-whisper imageio-ffmpeg tqdm
    ```
    不需要单独装系统级ffmpeg,切分部分直接调用imageio-ffmpeg自带的ffmpeg可执行文件(pip安装时会自动下载)。如果用GPU加速,需要提前安装好NVIDIA驱动+CUDA(faster-whisper底层依赖cuBLAS/cuDNN)。
  - 运行命令:
    ```
    python split_mp3_by_chapter.py input.mp3
    python split_mp3_by_chapter.py input.mp3 --model medium --device cuda --max-size 4
    ```
  - 参数说明:
    | 参数 | 是否必填 | 默认值 | 说明 |
    |---|---|---|---|
    | `audio`(位置参数) | ✅ | 无 | 输入的mp3文件路径 |
    | `--model` | ❌ | `base` | whisper模型大小,可选 `tiny`/`base`/`small`/`medium`/`large-v2`/`large-v3`,越大越准但越慢,GPU充足推荐 `large-v3` |
    | `--device` | ❌ | `cuda` | 推理设备,可选 `cuda`/`cpu`,没有可用GPU时需手动改成 `cpu` |
    | `--lang` | ❌ | `zh` | 语音识别的语言代码,中文音频用默认值即可 |
    | `--out` | ❌ | `chapters` | 切分结果的输出目录 |
    | `--min-gap` | ❌ | `5.0` | 章节标记去重的时间窗口(秒),同一章节标记短时间内重复出现会被合并为一个 |
    | `--max-size` | ❌ | `4.0` | 单个输出文件的最大体积(MB),超过会按时长再拆成 `_part1`、`_part2`...多段 |
    | `--bitrate` | ❌ | `64` | 导出mp3的码率(kbps),人声内容64kbps足够清晰且体积小 |
    | `--format` | ❌ | `mp3` | 输出的音频格式 |
  - 输出位置: `--out` 指定的目录下(默认是脚本运行目录下的 `chapters/` 文件夹),按检测到的章节顺序命名,例如 `00_序.mp3`、`01_第一章_part1.mp3`、`01_第一章_part2.mp3`...;序号前缀保证按文件名排序即为播放顺序

## :dolphin:运行环境
- Python **3.6+**(下载脚本中使用了 f-string 语法,低于3.6会直接报语法错误)
- 系统需要能在命令行直接调用 **ffmpeg**(`ffmpeg -version` 能正常输出):下载脚本合并多P视频(依赖moviepy)、`video_to_mp3.py` 转换音频都要用到
- 下面的 `requirements.txt` 只覆盖**下载脚本**(版本一~五)所需依赖;`video_to_mp3.py` 不需要额外pip依赖;`split_mp3_by_chapter.py` 的依赖(faster-whisper等)需单独安装,见对应小节
## :dolphin:安装依赖库
```
pip3 install -r requirements.txt
```