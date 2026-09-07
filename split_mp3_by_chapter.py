#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
根据音频里说出的"第一章""第二章"...等文字标记，自动把一个长 mp3 切分成多段；
每段如果超过指定大小（默认 4MB），会自动再按时长拆成更小的分段。

用的是 faster-whisper（比原版 openai-whisper 快很多，支持 GPU）。

依赖安装（本地终端执行，需要联网）：
    pip install faster-whisper imageio-ffmpeg tqdm

    不需要单独装系统级 ffmpeg：切分部分直接调用 imageio-ffmpeg 自带的
    ffmpeg 可执行文件（pip 装的时候会自动下载好），不依赖 ffprobe 或系统 PATH。

    如果用 GPU：确保装了 NVIDIA 驱动 + CUDA。faster-whisper 底层依赖
    cuBLAS / cuDNN，如果提示找不到 cublas64_12.dll / cudnn64_9.dll，装：
        pip install nvidia-cublas-cu12 nvidia-cudnn-cu12
    然后把这两个包的 bin 目录加到 PATH（详见对话记录），或加 --device cpu 先跑通。

用法：
    python split_mp3_by_chapter.py input.mp3
    python split_mp3_by_chapter.py input.mp3 --model medium --device cuda --max-size 4

conda activate bilibili_download
$env:Path = "D:\anaconda\envs\bilibili_download\lib\site-packages\nvidia\cublas\bin;D:\anaconda\envs\bilibili_download\lib\site-packages\nvidia\cudnn\bin;" + $env:Path
python split_mp3_by_chapter.py "F:\Bilibili_video_download-master\Bilibili_video_download-master\bilibili_video\《人间值得：90岁奶奶生活哲思小书》\[完本]  益家听书《人间值得：90岁奶奶生活哲思小书》( 完整).mp3" --device cuda

"""

import argparse
import math
import os
import re
import sys

from tqdm import tqdm

# ---------- 中文数字 -> 阿拉伯数字，用于章节排序/命名 ----------
_CN_NUM = {
    "零": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4, "五": 5,
    "六": 6, "七": 7, "八": 8, "九": 9, "十": 10,
}


def cn_to_int(s: str) -> int:
    """把'二十三' '一百零五' 这类中文数字转成 int；转不了就返回 -1"""
    if s.isdigit():
        return int(s)
    if not s:
        return -1
    total = 0
    try:
        if "百" in s:
            idx = s.index("百")
            bai = _CN_NUM.get(s[:idx], 1) if s[:idx] else 1
            total += bai * 100
            s = s[idx + 1:]
        if "十" in s:
            idx = s.index("十")
            shi = _CN_NUM.get(s[:idx], 1) if s[:idx] else 1
            total += shi * 10
            s = s[idx + 1:]
        if s:
            total += _CN_NUM.get(s, 0)
        return total if total > 0 else _CN_NUM.get(s, -1)
    except Exception:
        return -1


CHAPTER_PATTERN = re.compile(r"第([一二三四五六七八九十百零两\d]+)章")


def transcribe(audio_path: str, model_size: str, language: str, device: str):
    """用 faster-whisper 转写音频，返回统一格式的 segments 列表"""
    from faster_whisper import WhisperModel

    if device == "cuda":
        compute_type = "float16"
    else:
        compute_type = "int8"

    print(f"[1/3] 加载 faster-whisper 模型: {model_size} (device={device}, compute_type={compute_type}) ...")
    try:
        model = WhisperModel(model_size, device=device, compute_type=compute_type)
    except Exception as e:
        if device == "cuda":
            print(f"GPU 加载失败({e})，自动回退到 CPU（会比较慢）...")
            device = "cpu"
            model = WhisperModel(model_size, device="cpu", compute_type="int8")
        else:
            raise

    print("[2/3] 正在转写音频（GPU 上通常比原版 whisper 快 4-8 倍）...")
    segments_gen, info = model.transcribe(
        audio_path,
        language=language,
        word_timestamps=True,
        vad_filter=True,  # 过滤静音段，能再提速一些
    )

    total_duration = info.duration  # 音频总时长（秒），用于算进度条
    pbar = tqdm(total=round(total_duration, 1), unit="s",
                desc="转写进度", bar_format="{l_bar}{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}]")

    segments = []
    last_end = 0.0
    for seg in segments_gen:
        words = []
        if seg.words:
            for w in seg.words:
                words.append({"word": w.word, "start": w.start, "end": w.end})
        segments.append({
            "start": seg.start,
            "end": seg.end,
            "text": seg.text,
            "words": words,
        })

        # 更新进度条（按当前片段结束时间推进）
        pbar.update(min(seg.end, total_duration) - last_end)
        last_end = min(seg.end, total_duration)

        # 只有识别到章节关键字才额外打印一行，避免刷屏
        if CHAPTER_PATTERN.search(seg.text):
            pbar.write(f"  [检测到章节] {seg.start:8.1f}s  {seg.text.strip()}")

    pbar.close()
    return segments


def find_chapters(segments, min_gap_sec: float = 5.0):
    """在 segments 里查找章节标记，优先用词级时间戳定位到匹配文字开始的位置"""
    chapters = []

    for seg in segments:
        text = seg.get("text", "")
        for m in CHAPTER_PATTERN.finditer(text):
            raw_num = m.group(1)
            num = cn_to_int(raw_num)
            start_time = seg["start"]

            words = seg.get("words") or []
            if words:
                char_pos = 0
                for w in words:
                    w_text = w.get("word", "")
                    if char_pos <= m.start() < char_pos + len(w_text) + 2:
                        start_time = w.get("start", start_time)
                        break
                    char_pos += len(w_text)

            chapters.append({
                "raw": m.group(0),
                "num": num,
                "start": start_time,
                "context": text.strip(),
            })

    chapters.sort(key=lambda c: c["start"])
    deduped = []
    for c in chapters:
        if deduped and c["start"] - deduped[-1]["start"] < min_gap_sec:
            continue
        deduped.append(c)

    return deduped


def get_ffmpeg_exe() -> str:
    """获取 ffmpeg 可执行文件路径。优先用 imageio_ffmpeg 自带的（免安装），
    找不到再退回到系统 PATH 里的 ffmpeg。"""
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return "ffmpeg"  # 依赖系统 PATH


def get_duration_seconds(ffmpeg_exe: str, audio_path: str) -> float:
    """不依赖 ffprobe，直接用 ffmpeg -i 解析 stderr 里的 Duration 字段"""
    import subprocess
    result = subprocess.run(
        [ffmpeg_exe, "-i", audio_path],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        text=True, encoding="utf-8", errors="ignore",
    )
    m = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not m:
        raise RuntimeError("无法读取音频时长，ffmpeg 输出：\n" + result.stderr[-800:])
    h, mi, s = m.groups()
    return int(h) * 3600 + int(mi) * 60 + float(s)


def ffmpeg_cut(ffmpeg_exe: str, input_path: str, start_sec: float, end_sec: float,
               output_path: str, bitrate_kbps: int):
    """用 ffmpeg 精确剪切并按固定码率重新编码为 mp3，控制输出体积可预估"""
    import subprocess
    duration = max(0.05, end_sec - start_sec)
    cmd = [
        ffmpeg_exe, "-y",
        "-ss", f"{start_sec:.3f}",
        "-i", input_path,
        "-t", f"{duration:.3f}",
        "-vn",
        "-ar", "44100",
        "-b:a", f"{bitrate_kbps}k",
        output_path,
    ]
    proc = subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
                           text=True, encoding="utf-8", errors="ignore")
    if proc.returncode != 0:
        raise RuntimeError(f"ffmpeg 切分失败: {output_path}\n{proc.stderr[-800:]}")


def export_with_size_limit(ffmpeg_exe, audio_path, start_sec, end_sec, base_path_no_ext,
                            fmt, bitrate_kbps, max_size_bytes):
    """
    导出 [start_sec, end_sec) 区间。如果按给定码率估算会超过 max_size_bytes，
    自动按时长切成多段，每段导出为 base_path_no_ext_partN.fmt。
    用固定码率导出，保证大小可预估、不超限（留了约 10% 安全余量）。
    """
    duration_sec = end_sec - start_sec
    bitrate_bps = bitrate_kbps * 1000
    max_duration_sec = (max_size_bytes * 8 / bitrate_bps) * 0.9  # 留 10% 余量

    exported = []

    if duration_sec <= max_duration_sec:
        path = f"{base_path_no_ext}.{fmt}"
        ffmpeg_cut(ffmpeg_exe, audio_path, start_sec, end_sec, path, bitrate_kbps)
        exported.append(path)
    else:
        n_parts = math.ceil(duration_sec / max_duration_sec)
        part_len = duration_sec / n_parts
        for i in range(n_parts):
            p_start = start_sec + i * part_len
            p_end = min(start_sec + (i + 1) * part_len, end_sec)
            path = f"{base_path_no_ext}_part{i+1}.{fmt}"
            ffmpeg_cut(ffmpeg_exe, audio_path, p_start, p_end, path, bitrate_kbps)
            exported.append(path)

    return exported


def split_audio(audio_path: str, chapters: list, out_dir: str, fmt: str,
                 bitrate_kbps: int, max_size_mb: float):
    ffmpeg_exe = get_ffmpeg_exe()
    print(f"[3/3] 正在切分并导出音频（使用 ffmpeg: {ffmpeg_exe}）...")

    os.makedirs(out_dir, exist_ok=True)
    total_sec = get_duration_seconds(ffmpeg_exe, audio_path)
    max_size_bytes = int(max_size_mb * 1024 * 1024)

    if not chapters:
        print("未检测到任何章节标记，未做切分。")
        return

    all_exported = []

    if chapters[0]["start"] > 3.0:
        base = os.path.join(out_dir, "00_序")
        files = export_with_size_limit(ffmpeg_exe, audio_path, 0, chapters[0]["start"],
                                        base, fmt, bitrate_kbps, max_size_bytes)
        all_exported.extend(files)
        for f in files:
            print(f"  导出: {f}")

    for i, ch in enumerate(chapters):
        start_sec = ch["start"]
        end_sec = chapters[i + 1]["start"] if i + 1 < len(chapters) else total_sec

        num = ch["num"] if ch["num"] > 0 else i + 1
        base = os.path.join(out_dir, f"{num:02d}_{ch['raw']}")
        files = export_with_size_limit(ffmpeg_exe, audio_path, start_sec, end_sec, base,
                                        fmt, bitrate_kbps, max_size_bytes)
        all_exported.extend(files)
        for f in files:
            size_mb = os.path.getsize(f) / (1024 * 1024)
            print(f"  导出: {f}  ({size_mb:.2f} MB)")

    print(f"\n完成！共导出 {len(all_exported)} 个文件到目录: {out_dir}")


def main():
    parser = argparse.ArgumentParser(description="根据语音中的章节标记自动切分 mp3，并限制单文件大小")
    parser.add_argument("audio", help="输入的 mp3 文件路径")
    parser.add_argument("--model", default="base",
                         choices=["tiny", "base", "small", "medium", "large-v2", "large-v3"],
                         help="whisper 模型大小，默认 medium。GPU 充足可以用 large-v3 提升准确率")
    parser.add_argument("--device", default="cuda", choices=["cuda", "cpu"],
                         help="推理设备，默认 cuda（没有可用 GPU 会自动回退到 cpu）")
    parser.add_argument("--lang", default="zh", help="语言代码，默认 zh（中文）")
    parser.add_argument("--out", default="chapters", help="输出目录，默认 chapters")
    parser.add_argument("--min-gap", type=float, default=5.0,
                         help="章节去重时间窗口(秒)，默认 5")
    parser.add_argument("--max-size", type=float, default=4.0,
                         help="单个输出文件最大体积(MB)，默认 4")
    parser.add_argument("--bitrate", type=int, default=64,
                         help="导出 mp3 码率(kbps)，默认 64，人声足够清晰且体积小")
    parser.add_argument("--format", default="mp3", help="输出格式，默认 mp3")
    args = parser.parse_args()

    if not os.path.isfile(args.audio):
        print(f"找不到文件: {args.audio}")
        sys.exit(1)

    segments = transcribe(args.audio, args.model, args.lang, args.device)
    chapters = find_chapters(segments, min_gap_sec=args.min_gap)

    if chapters:
        print(f"\n检测到 {len(chapters)} 个章节标记：")
        for c in chapters:
            print(f"  {c['raw']:<6}  @ {c['start']:7.1f}s   ...{c['context'][:30]}...")
    else:
        print("\n未检测到任何'第X章'格式的标记，请检查音频内容或调整 CHAPTER_PATTERN 正则表达式。")
        sys.exit(0)

    split_audio(args.audio, chapters, args.out, args.format, args.bitrate, args.max_size)


if __name__ == "__main__":
    main()