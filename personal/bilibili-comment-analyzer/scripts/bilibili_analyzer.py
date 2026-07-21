#!/usr/bin/env python3
"""
B站 UP主评论采集与分析工具
===========================
爬取指定UP主稿件的评论，进行情感分析、词云、关键词提取、观点分类等
输出：控制台摘要 + Excel报表 + HTML报告
"""

import argparse
import json
import os
import re
import sys
import time
import traceback
from collections import Counter
from datetime import datetime
from typing import Optional

# Windows GBK编码兼容处理
if sys.platform == 'win32' and sys.stdout.encoding and sys.stdout.encoding.upper() in ('GBK', 'GB2312', 'CP936'):
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# ====== 第三方库导入 ======
try:
    import jieba
    import jieba.analyse
except ImportError:
    print("[错误] 缺少 jieba 库，请运行: pip3 install --user --break-system-packages jieba")
    sys.exit(1)

try:
    import pandas as pd
except ImportError:
    print("[错误] 缺少 pandas 库，请运行: pip3 install --user --break-system-packages pandas")
    sys.exit(1)

try:
    from snownlp import SnowNLP
except ImportError:
    print("[错误] 缺少 snownlp 库，请运行: pip3 install --user --break-system-packages snownlp")
    sys.exit(1)

try:
    import matplotlib
    matplotlib.use('Agg')  # WSL无显示器，使用Agg后端
    import matplotlib.pyplot as plt
except ImportError:
    print("[错误] 缺少 matplotlib 库，请运行: pip3 install --user --break-system-packages matplotlib")
    sys.exit(1)

try:
    from wordcloud import WordCloud
except ImportError:
    print("[错误] 缺少 wordcloud 库，请运行: pip3 install --user --break-system-packages wordcloud")
    sys.exit(1)

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    from openpyxl.utils import get_column_letter
except ImportError:
    print("[错误] 缺少 openpyxl 库，请运行: pip3 install --user --break-system-packages openpyxl")
    sys.exit(1)

# ====== bilibili-api ======
BILIBILI_IMPORT_OK = False
bili_user = None
bili_video = None
bili_comment = None
bili_sync = None

try:
    from bilibili_api import sync, user, video, comment
    from bilibili_api import Credential, HEADERS as BILI_HEADERS_DICT
    bili_user = user
    bili_video = video
    bili_comment = comment
    bili_sync = sync
    bili_credential = Credential
    BILIBILI_IMPORT_OK = True
except ImportError:
    print("[错误] 缺少 bilibili-api-python 库，请运行: pip3 install --user --break-system-packages bilibili-api-python")
    sys.exit(1)

# ====== 全局配置 ======
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_DIR = os.path.dirname(SCRIPT_DIR)

GLOBAL_CREDENTIAL = None  # 将在main中初始化

STOP_WORDS = set("""
的 了 在 是 我 有 和 就 不 人 都 一 一个 上 也 很 到 说 要 去 你
会 着 没有 看 好 自己 这 他 她 它 们 那 什么 吧 吗 啊 哦 嗯 哈
呀 呢 啦 呗 嘛 哟 呵 嗨 哎 喂 唔 吖 哇 诶 得了 就是 但是 因为
所以 虽然 然而 而且 如果 那么 只是 还是 或者 不过 这个 那个
怎么 为什么 如何 哪些 哪里 何时 可以 应该 能够 需要 已经
还 没 更 再 又 才 也 都 只 就 便 却 则 及 与 跟 被 把 将
让 给 对 从 向 往 在 到 于 以 为 比 除了 关于 通过 根据
按照 沿 靠 用 拿 替 同 随 作为 当作 本着 经过 当
一 二 三 四 五 六 七 八 九 十 百 千 万 亿 两
个 只 条 位 种 次 回 下 遍 番 趟 顿 场 块 张 件 根 颗 片 面
点 些 的 地 得 着 了 过
up 视频 主播 大佬 大神 老师 觉得 感觉 真的 这个 一个 没有
""".split())

# ========================================================================
#                         第一部分：B站数据采集
# ========================================================================

def get_up_mid_from_input(mid_input: str) -> int:
    """从输入中提取UP主mid"""
    mid_input = mid_input.strip()
    # 如果是space.bilibili.com/xxx 格式
    match = re.search(r'space\.bilibili\.com/(\d+)', mid_input)
    if match:
        return int(match.group(1))
    # 纯数字
    if mid_input.isdigit():
        return int(mid_input)
    raise ValueError(f"无法解析UP主mid: {mid_input}，请使用纯数字mid或space.bilibili.com/xxx链接")


def fetch_up_videos(mid: int, limit: int = 50) -> list:
    """获取UP主所有视频稿件列表"""
    u = bili_user.User(mid, credential=GLOBAL_CREDENTIAL) if GLOBAL_CREDENTIAL else bili_user.User(mid)
    videos = []
    page = 1
    while True:
        try:
            print(f"  [采集] 获取第 {page} 页视频列表...")
            result = bili_sync(u.get_videos(ps=30, pn=page))
            if not result or 'list' not in result or 'vlist' not in result['list']:
                break
            vlist = result['list']['vlist']
            if not vlist:
                break
            for v in vlist:
                videos.append({
                    'aid': v['aid'],
                    'bvid': v.get('bvid', ''),
                    'title': v.get('title', '').strip(),
                    'description': v.get('description', '').strip(),
                    'play': v.get('play', 0),
                    'comment': v.get('comment', 0),
                    'video_review': v.get('video_review', 0),
                    'favorites': v.get('favorites', 0),
                    'mid': v.get('mid', mid),
                    'author': v.get('author', ''),
                    'created': v.get('created', 0),
                    'length': v.get('length', ''),
                    'pic': v.get('pic', ''),
                })
            page += 1
            if limit > 0 and len(videos) >= limit:
                videos = videos[:limit]
                break
            time.sleep(0.5)
        except Exception as e:
            print(f"  [警告] 获取视频列表第{page}页出错: {e}")
            time.sleep(2)
            break
    print(f"  [完成] 共获取到 {len(videos)} 个视频")
    return videos


def fetch_video_comments(aid: int, pages: int = 10, sort: int = 2) -> list:
    """获取一个视频的评论（热评排序）"""
    all_comments = []
    for pn in range(1, pages + 1):
        try:
            result = bili_sync(
                bili_comment.get_comments(
                    aid,
                    bili_comment.ResourceType.VIDEO,
                    page_index=pn,
                    order=sort,  # 2=热度, 0=时间
                )
            ) if not GLOBAL_CREDENTIAL else bili_sync(
                bili_comment.get_comments(
                    aid,
                    bili_comment.ResourceType.VIDEO,
                    page_index=pn,
                    order=sort,
                    credential=GLOBAL_CREDENTIAL,
                )
            )
            replies = result.get('replies', [])
            if not replies:
                break
            for r in replies:
                all_comments.append({
                    'rpid': r.get('rpid', 0),
                    'oid': aid,
                    'uid': r.get('member', {}).get('mid', 0),
                    'uname': r.get('member', {}).get('uname', ''),
                    'content': r.get('content', {}).get('message', ''),
                    'like': r.get('like', 0),
                    'rcount': r.get('rcount', 0),  # 回复数
                    'ctime': r.get('ctime', 0),
                    'sex': r.get('member', {}).get('sex', '保密'),
                    'level': r.get('member', {}).get('level_info', {}).get('current_level', 0),
                })
            time.sleep(0.3)
        except Exception as e:
            print(f"    [警告] 评论第{pn}页出错: {e}")
            time.sleep(1)
            break
    return all_comments


def collect_all_data(mid: int, pages: int = 10, limit_videos: int = 50, sort: int = 2) -> tuple:
    """采集UP主所有视频 + 评论"""
    print(f"\n{'='*60}")
    print(f"  开始采集 UP主 mid={mid}")
    print(f"{'='*60}")

    # 1. 获取视频列表
    videos = fetch_up_videos(mid, limit=limit_videos)
    if not videos:
        print("[错误] 未获取到任何视频，请检查mid是否正确")
        return [], []

    print(f"\n  共 {len(videos)} 个视频，开始采集评论...")

    # 2. 逐个获取评论
    all_comments = []
    for i, v in enumerate(videos):
        print(f"  [{i+1}/{len(videos)}] {v['title'][:40]}...", end='', flush=True)
        comments = fetch_video_comments(v['aid'], pages=pages, sort=sort)
        for c in comments:
            c['video_title'] = v['title']
            c['video_aid'] = v['aid']
            c['video_bvid'] = v['bvid']
            c['video_play'] = v['play']
        all_comments.extend(comments)
        print(f" {len(comments)}条评论")
        time.sleep(0.5)

    print(f"\n{'='*60}")
    print(f"  采集完成！共 {len(videos)} 个视频，{len(all_comments)} 条评论")
    print(f"{'='*60}")

    return videos, all_comments


# ========================================================================
#                         第二部分：文本分析与NLP
# ========================================================================

def preprocess_text(text: str) -> str:
    """清洗评论文本"""
    if not text:
        return ""
    # 去除HTML标签
    text = re.sub(r'<[^>]+>', '', text)
    # 去除URL
    text = re.sub(r'https?://\S+', '', text)
    # 去除@提及
    text = re.sub(r'@\S+', '', text)
    # 去除多余空白
    text = re.sub(r'\s+', ' ', text).strip()
    return text


def sentiment_score(text: str) -> float:
    """情感分析，返回0-1分数（>0.5积极）"""
    try:
        if not text or len(text) < 2:
            return 0.5
        return SnowNLP(text).sentiments
    except:
        return 0.5


def classify_sentiment(score: float) -> str:
    """分类情感"""
    if score >= 0.65:
        return "正面"
    elif score <= 0.35:
        return "负面"
    return "中性"


def extract_keywords(texts: list, topk: int = 30) -> list:
    """提取关键词（TF-IDF）"""
    full_text = ' '.join(texts)
    if not full_text.strip():
        return []
    try:
        keywords = jieba.analyse.extract_tags(full_text, topK=topk, withWeight=True)
        return [{'word': w, 'weight': round(f, 4)} for w, f in keywords]
    except:
        return []


def cut_words(texts: list, stop_words: set = None) -> list:
    """分词"""
    if stop_words is None:
        stop_words = STOP_WORDS
    words = []
    for text in texts:
        cleaned = preprocess_text(text.lower())
        if not cleaned:
            continue
        for w in jieba.cut(cleaned):
            w = w.strip()
            if len(w) >= 2 and w not in stop_words and not re.match(r'^[0-9a-zA-Z\s]+$', w):
                words.append(w)
    return words


def get_word_freq(words: list, topk: int = 50) -> list:
    """词频统计"""
    counter = Counter(words)
    return [{'word': w, 'count': c} for w, c in counter.most_common(topk)]


# ========================================================================
#                         第三部分：可视化与报表生成
# ========================================================================

def find_chinese_font() -> str:
    """查找系统中可用的中文字体"""
    import matplotlib.font_manager as fm
    # 常见中文字体
    font_candidates = [
        'WenQuanYi Micro Hei',
        'Noto Sans CJK SC',
        'Noto Sans SC',
        'SimHei',
        'Microsoft YaHei',
        'STHeiti',
        'Source Han Sans SC',
        'FangSong',
        'KaiTi',
        'AR PL UMing CN',
        'AR PL UKai CN',
    ]
    available = [f.name for f in fm.fontManager.ttflist]
    for fname in font_candidates:
        if fname in available:
            return fname
    # fallback: 找任何带CJK/Hei/Song的字体
    for f in available:
        if any(k in f.lower() for k in ['noto', 'cjk', 'hei', 'song', 'ming', 'fang']):
            return f
    return None


def generate_wordcloud(words: list, font_path: str = None) -> Optional[str]:
    """生成词云图，返回图片路径"""
    if not words:
        return None
    word_freq = {w['word']: max(1, w['count']) for w in words}
    try:
        wc = WordCloud(
            font_path=font_path,
            width=1200,
            height=800,
            background_color='white',
            max_words=200,
            max_font_size=120,
            random_state=42,
            colormap='viridis',
        )
        wc.generate_from_frequencies(word_freq)
        img_path = os.path.join(output_dir, 'wordcloud.png')
        wc.to_file(img_path)
        return img_path
    except Exception as e:
        print(f"  [警告] 生成词云失败: {e}")
        return None


def generate_sentiment_chart(sentiments: list, output_dir: str) -> Optional[str]:
    """生成情感分布饼图和柱状图"""
    if not sentiments:
        return None
    counts = Counter(sentiments)
    labels = ['正面', '中性', '负面']
    values = [counts.get('正面', 0), counts.get('中性', 0), counts.get('负面', 0)]
    colors = ['#4CAF50', '#FFC107', '#F44336']

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    fig.suptitle('评论情感分析', fontsize=16, fontproperties=font_prop)

    # 饼图
    ax1.pie(values, labels=labels, autopct='%1.1f%%', colors=colors,
            startangle=90, textprops={'fontproperties': font_prop})
    ax1.set_title('情感分布', fontproperties=font_prop)

    # 柱状图
    bars = ax2.bar(labels, values, color=colors)
    ax2.set_title('情感数量对比', fontproperties=font_prop)
    ax2.set_ylabel('评论数', fontproperties=font_prop)
    for bar, val in zip(bars, values):
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1,
                 str(val), ha='center', fontproperties=font_prop)
    for label in ax2.get_xticklabels() + ax2.get_yticklabels():
        label.set_fontproperties(font_prop)

    plt.tight_layout()
    img_path = os.path.join(output_dir, 'sentiment_chart.png')
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    return img_path


def generate_trend_chart(comments_df: pd.DataFrame, output_dir: str) -> Optional[str]:
    """生成情感趋势折线图（按视频发布时间排序）"""
    if comments_df.empty or 'sentiment_cat' not in comments_df.columns:
        return None
    try:
        # 按视频分组统计情感
        grouped = comments_df.groupby('video_title').agg(
            正面=('sentiment_cat', lambda x: (x == '正面').sum()),
            中性=('sentiment_cat', lambda x: (x == '中性').sum()),
            负面=('sentiment_cat', lambda x: (x == '负面').sum()),
        ).head(20)

        if grouped.empty:
            return None

        fig, ax = plt.subplots(figsize=(14, 6))
        grouped.plot(kind='bar', stacked=True, ax=ax,
                     color=['#4CAF50', '#FFC107', '#F44336'])
        ax.set_title('各视频评论情感分布（Top 20）', fontproperties=font_prop, fontsize=14)
        ax.set_xlabel('视频', fontproperties=font_prop)
        ax.set_ylabel('评论数', fontproperties=font_prop)
        ax.legend(prop=font_prop)
        plt.xticks(rotation=45, ha='right', fontproperties=font_prop)
        for label in ax.get_yticklabels():
            label.set_fontproperties(font_prop)
        plt.tight_layout()
        img_path = os.path.join(output_dir, 'sentiment_trend.png')
        plt.savefig(img_path, dpi=150, bbox_inches='tight')
        plt.close()
        return img_path
    except:
        return None


def generate_top_comments_chart(top_comments: list, output_dir: str) -> Optional[str]:
    """生成热评排行榜图"""
    if not top_comments:
        return None
    top10 = top_comments[:10][::-1]  # 倒序让最高的在上面
    texts = [re.sub(r'[\n\r]', ' ', c['content'])[:30] + '...' if len(c['content']) > 30
             else re.sub(r'[\n\r]', ' ', c['content']) for c in top10]
    likes = [c['like'] for c in top10]

    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(texts)), likes, color='#FF6B6B')
    ax.set_yticks(range(len(texts)))
    ax.set_yticklabels(texts, fontproperties=font_prop)
    ax.set_xlabel('点赞数', fontproperties=font_prop)
    ax.set_title('热评排行榜（Top 10）', fontproperties=font_prop, fontsize=14)
    for bar, val in zip(bars, likes):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                str(val), ha='left', va='center', fontproperties=font_prop)
    for label in ax.get_xticklabels():
        label.set_fontproperties(font_prop)
    plt.tight_layout()
    img_path = os.path.join(output_dir, 'top_comments.png')
    plt.savefig(img_path, dpi=150, bbox_inches='tight')
    plt.close()
    return img_path


# ========================================================================
#                         第四部分：Excel报表
# ========================================================================

def write_excel(videos: list, comments: list, keywords: list,
                word_freq: list, sentiment_dist: dict, output_dir: str) -> str:
    """生成多sheet Excel报表"""
    excel_path = os.path.join(output_dir, 'bilibili_report.xlsx')
    writer = pd.ExcelWriter(excel_path, engine='openpyxl')

    # Sheet 1: 原始评论数据
    df_comments = pd.DataFrame(comments)
    if not df_comments.empty:
        cols = ['uname', 'content', 'like', 'rcount', 'sentiment', 'sentiment_cat',
                'video_title', 'video_play', 'sex', 'level', 'ctime']
        cols = [c for c in cols if c in df_comments.columns]
        df_comments[cols].to_excel(writer, sheet_name='评论原始数据', index=False)
        # 调整列宽
        ws = writer.sheets['评论原始数据']
        ws.column_dimensions['B'].width = 60
        ws.column_dimensions['G'].width = 40

    # Sheet 2: 视频列表
    df_videos = pd.DataFrame(videos)
    if not df_videos.empty:
        df_videos.to_excel(writer, sheet_name='视频列表', index=False)

    # Sheet 3: 情感分布
    if sentiment_dist:
        df_sent = pd.DataFrame([
            {'情感分类': k, '数量': v, '占比': f"{v/sum(sentiment_dist.values())*100:.1f}%"}
            for k, v in sentiment_dist.items()
        ])
        df_sent.to_excel(writer, sheet_name='情感分析', index=False)

    # Sheet 4: 高频词
    if word_freq:
        df_words = pd.DataFrame(word_freq)
        df_words.to_excel(writer, sheet_name='高频词汇', index=False)

    # Sheet 5: 关键词TF-IDF
    if keywords:
        df_kw = pd.DataFrame(keywords)
        df_kw.to_excel(writer, sheet_name='关键词(TF-IDF)', index=False)

    # Sheet 6: 热评排行
    hot = sorted(comments, key=lambda x: x.get('like', 0), reverse=True)[:50]
    if hot:
        df_hot = pd.DataFrame(hot)
        cols = ['uname', 'content', 'like', 'rcount', 'video_title']
        cols = [c for c in cols if c in df_hot.columns]
        df_hot[cols].to_excel(writer, sheet_name='热评排行榜Top50', index=False)
        ws = writer.sheets['热评排行榜Top50']
        ws.column_dimensions['B'].width = 60

    # 格式化：标题行加粗
    for sheet_name in writer.sheets:
        ws = writer.sheets[sheet_name]
        header_font = Font(bold=True, size=11)
        for cell in ws[1]:
            cell.font = header_font

    writer.close()
    return excel_path


# ========================================================================
#                         第五部分：HTML报告
# ========================================================================

def generate_html_report(up_name: str, mid: int, videos: list, comments: list,
                          keywords: list, word_freq: list, sentiment_dist: dict,
                          top_hot: list, images: dict, report_name: str = "") -> str:
    """生成可读性强的HTML报告"""
    if not report_name:
        report_name = f"UP主{mid}评论分析报告"

    total_videos = len(videos)
    total_comments = len(comments)
    total_likes = sum(c.get('like', 0) for c in comments)
    avg_sentiment = round(sum(c.get('sentiment', 0.5) for c in comments) / max(1, len(comments)), 2)

    positive = sentiment_dist.get('正面', 0)
    negative = sentiment_dist.get('负面', 0)
    neutral = sentiment_dist.get('中性', 0)

    # 构建关键词HTML
    kw_html = ""
    if keywords:
        max_w = keywords[0]['weight']
        kw_html = '<div class="keywords">'
        for kw in keywords[:20]:
            size = max(12, int(24 * kw['weight'] / max_w))
            kw_html += f'<span style="font-size:{size}px;margin:4px">{kw["word"]}</span>'
        kw_html += '</div>'

    # 词云图片
    img_wordcloud = images.get('wordcloud', '')
    img_sentiment = images.get('sentiment', '')
    img_trend = images.get('trend', '')
    img_top = images.get('top_comments', '')

    # 热评表格
    hot_rows = ""
    for i, c in enumerate(top_hot[:20], 1):
        hot_rows += f"""
        <tr>
            <td>{i}</td>
            <td>{c.get('uname', '')}</td>
            <td class="content-cell">{c.get('content', '')}</td>
            <td>{c.get('like', 0)}</td>
            <td>{c.get('rcount', 0)}</td>
            <td>{c.get('sentiment_cat', '')}</td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{report_name}</title>
<style>
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: -apple-system, 'Microsoft YaHei', sans-serif; background: #f5f7fa; color: #333; }}
.header {{ background: linear-gradient(135deg, #fb7299, #fc8bab); color: white; padding: 40px; text-align: center; }}
.header h1 {{ font-size: 28px; margin-bottom: 10px; }}
.header p {{ opacity: 0.9; font-size: 14px; }}
.stats {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; padding: 30px; max-width: 1200px; margin: 0 auto; }}
.stat-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); text-align: center; }}
.stat-card .num {{ font-size: 32px; font-weight: bold; color: #fb7299; }}
.stat-card .label {{ font-size: 14px; color: #999; margin-top: 5px; }}
.section {{ max-width: 1200px; margin: 0 auto; padding: 20px 30px; }}
.section h2 {{ font-size: 22px; margin-bottom: 20px; border-left: 4px solid #fb7299; padding-left: 12px; }}
.chart-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-bottom: 30px; }}
.chart-grid .full {{ grid-column: 1 / -1; }}
.chart-card {{ background: white; border-radius: 12px; padding: 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
.chart-card img {{ width: 100%; height: auto; border-radius: 8px; }}
.keywords {{ display: flex; flex-wrap: wrap; align-items: center; justify-content: center; padding: 20px; }}
.keywords span {{ display: inline-block; padding: 4px 12px; margin: 4px; background: #f0f0f5; border-radius: 16px; }}
table {{ width: 100%; border-collapse: collapse; background: white; border-radius: 12px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.08); }}
th {{ background: #fb7299; color: white; padding: 12px 16px; text-align: left; font-size: 14px; }}
td {{ padding: 10px 16px; border-bottom: 1px solid #eee; font-size: 13px; }}
tr:hover {{ background: #fafafa; }}
.content-cell {{ max-width: 400px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
.footer {{ text-align: center; padding: 30px; color: #999; font-size: 12px; }}
@media (max-width: 768px) {{ .chart-grid {{ grid-template-columns: 1fr; }} .stats {{ grid-template-columns: 1fr 1fr; }} }}
</style>
</head>
<body>
<div class="header">
    <h1>{report_name}</h1>
    <p>UP主: {up_name} (mid: {mid}) | 分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
</div>

<div class="stats">
    <div class="stat-card"><div class="num">{total_videos}</div><div class="label">采集视频数</div></div>
    <div class="stat-card"><div class="num">{total_comments}</div><div class="label">评论总数</div></div>
    <div class="stat-card"><div class="num">{total_likes:,}</div><div class="label">总点赞数</div></div>
    <div class="stat-card"><div class="num">{avg_sentiment}</div><div class="label">平均情感分</div></div>
    <div class="stat-card"><div class="num" style="color:#4CAF50">{positive}</div><div class="label">正面评论</div></div>
    <div class="stat-card"><div class="num" style="color:#F44336">{negative}</div><div class="label">负面评论</div></div>
</div>

<div class="section">
    <h2>📊 情感分析</h2>
    <div class="chart-grid">
        <div class="chart-card">
            <img src="{os.path.basename(img_sentiment) if img_sentiment else ''}" alt="情感分布">
        </div>
        <div class="chart-card">
            <h3 style="margin-bottom:15px">关键词云</h3>
            {kw_html if not img_wordcloud else ''}
            {'<img src="' + os.path.basename(img_wordcloud) + '" alt="词云">' if img_wordcloud else ''}
        </div>
        {'<div class="chart-card full"><img src="' + os.path.basename(img_trend) + '" alt="情感趋势"></div>' if img_trend else ''}
    </div>
</div>

<div class="section">
    <h2>🔥 热评排行榜（Top 20）</h2>
    <table>
    <thead><tr><th>#</th><th>用户</th><th>评论内容</th><th>👍点赞</th><th>💬回复</th><th>情感</th></tr></thead>
    <tbody>{hot_rows}</tbody>
    </table>
</div>

<div class="section">
    <h2>🏆 热评词云</h2>
    <div class="chart-card full">
        {'<img src="' + os.path.basename(img_top) + '" alt="热评排行">' if img_top else '<p>暂无数据</p>'}
    </div>
</div>

<div class="section">
    <h2>📈 高频词汇（Top 50）</h2>
    <div class="keywords">
    {''.join(f'<span>{w["word"]} <small>({w["count"]})</small></span>' for w in word_freq[:30])}
    </div>
</div>

<div class="section">
    <h2>🔑 关键词（TF-IDF）</h2>
    <div class="keywords">
    {''.join(f'<span style="font-size:14px;background:#e3f2fd">{kw["word"]} <small>({kw["weight"]})</small></span>' for kw in keywords[:20])}
    </div>
</div>

<div class="footer">
    <p>B站评论分析工具 | 报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
</div>
</body>
</html>"""
    html_path = os.path.join(output_dir, 'report.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    return html_path


# ========================================================================
#                         第六部分：控制台输出
# ========================================================================

def print_console_summary(videos: list, comments: list, sentiment_dist: dict,
                          keywords: list, word_freq: list, top_hot: list):
    """在控制台输出分析摘要"""
    total_comments = len(comments)
    print(f"\n{'='*60}")
    print(f"  📊 B站评论分析报告")
    print(f"{'='*60}")
    print(f"  视频数:    {len(videos)}")
    print(f"  评论数:    {total_comments}")
    print(f"  总点赞:    {sum(c.get('like', 0) for c in comments):,}")
    print(f"  平均情感分: {sum(c.get('sentiment', 0.5) for c in comments) / max(1, total_comments):.2f}")
    print(f"{'─'*60}")

    # 情感分布
    if sentiment_dist:
        total = sum(sentiment_dist.values())
        print(f"  📈 情感分布:")
        for k, v in sentiment_dist.items():
            pct = v / total * 100
            bar = '█' * int(pct / 2)
            print(f"    {k}: {bar} {v}条 ({pct:.1f}%)")
        print(f"{'─'*60}")

    # 高频词Top 15
    if word_freq:
        print(f"  🔤 高频词汇 Top 15:")
        for i, w in enumerate(word_freq[:15], 1):
            print(f"    {i:2d}. {w['word']:8s} × {w['count']}")
        print(f"{'─'*60}")

    # 关键词Top 10
    if keywords:
        print(f"  🔑 关键词 Top 10 (TF-IDF):")
        for i, kw in enumerate(keywords[:10], 1):
            print(f"    {i:2d}. {kw['word']:8s} (权重: {kw['weight']})")
        print(f"{'─'*60}")

    # 热评Top 5
    if top_hot:
        print(f"  🔥 热评 Top 5:")
        for i, c in enumerate(top_hot[:5], 1):
            content = c.get('content', '')[:50] + '...' if len(c.get('content', '')) > 50 else c.get('content', '')
            print(f"    {i}. [{c.get('like', 0)}👍] {c.get('uname', '')}: {content}")
        print(f"{'─'*60}")

    # 负面评论预览（情感分最低的5条）
    negative = sorted(comments, key=lambda x: x.get('sentiment', 0.5))[:5]
    if negative and negative[0].get('sentiment', 0.5) < 0.35:
        print(f"  ⚠️  负面评论示例:")
        for c in negative:
            content = c.get('content', '')[:40] + '...' if len(c.get('content', '')) > 40 else c.get('content', '')
            print(f"    [{c.get('sentiment', 0):.2f}分] {c.get('uname', '')}: {content}")

    print(f"{'='*60}")


# ========================================================================
#                         主流程
# ========================================================================

output_dir = ""  # 全局，供函数使用
font_prop = None  # 全局字体属性


def main():
    global output_dir, font_prop, GLOBAL_CREDENTIAL

    parser = argparse.ArgumentParser(
        description='B站UP主评论采集与分析工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  %(prog)s --mid 43683678                    # 基础分析
  %(prog)s --mid 43683678 --pages 5           # 只取前5页
  %(prog)s --mid space.bilibili.com/xxx       # 支持空间链接
  %(prog)s --mid 43683678 --limit-videos 10   # 限10个视频
  %(prog)s --mid 43683678 --no-html           # 不生成HTML报告
  %(prog)s --mid 43683678 --cookie "SESSDATA=xxx; bili_jct=yyy"  # 带Cookie防412
  %(prog)s --mid 43683678 --sessdata xxx --bili-jct yyy         # 分开传更安全
  env BILI_SESSDATA=xxx BILI_JCT=yyy %(prog)s --mid 43683678     # 环境变量最安全
        """
    )
    parser.add_argument('--mid', type=str, required=True, help='UP主mid数字或空间链接')
    parser.add_argument('--pages', type=int, default=10, help='每个视频采集评论页数（每页20条），默认10')
    parser.add_argument('--limit-videos', type=int, default=50, help='最多采集视频数，0=不限制，默认50')
    parser.add_argument('--sort', type=int, default=2, choices=[0, 2], help='评论排序: 2=热度(默认), 0=时间')
    parser.add_argument('--output', type=str, default='', help='输出目录（默认自动生成）')
    parser.add_argument('--no-html', action='store_true', help='跳过HTML报告生成')
    parser.add_argument('--no-excel', action='store_true', help='跳过Excel报表生成')
    parser.add_argument('--name', type=str, default='', help='给分析命名')
    parser.add_argument('--cookie', type=str, default='',
                        help='B站登录Cookie字符串（绕过412风控）。从浏览器F12→Application→Cookies→bilibili.com复制SESSDATA和bili_jct')
    parser.add_argument('--sessdata', type=str, default='',
                        help='仅设置SESSDATA值（更安全，避免在命令行暴露完整Cookie）。也可通过环境变量 BILI_SESSDATA 设置')
    parser.add_argument('--bili-jct', type=str, default='',
                        help='bili_jct 值，配合 --sessdata 使用。也可通过环境变量 BILI_JCT 设置')
    args = parser.parse_args()

    # ---- 解析mid ----
    try:
        mid = get_up_mid_from_input(args.mid)
    except ValueError as e:
        print(f"[错误] {e}")
        sys.exit(1)

    # ---- 输出目录 ----
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    if args.output:
        output_dir = os.path.join(args.output, f'bilibili_report_{timestamp}')
    else:
        output_dir = f'bilibili_report_{timestamp}'
    os.makedirs(output_dir, exist_ok=True)

    # ---- 设置B站API全局请求头（模拟浏览器） ----
    try:
        BILI_HEADERS_DICT.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
            'Referer': 'https://www.bilibili.com/',
            'Origin': 'https://www.bilibili.com',
        })
        print("  [网络] 已设置浏览器模拟请求头")
    except Exception as e:
        print(f"  [网络] 设置请求头失败: {e}")

    # ---- 中文字体设置 ----
    font_name = find_chinese_font()
    if font_name:
        font_prop = matplotlib.font_manager.FontProperties(family=font_name)
        print(f"  [字体] 使用: {font_name}")
    else:
        font_prop = None
        print("  [警告] 未找到中文字体，图表中文可能显示异常")

    # ---- Cookie / Credential 设置 ----
    global GLOBAL_CREDENTIAL
    
    # 优先级：--cookie > --sessdata/--bili-jct > 环境变量
    cookie_str = args.cookie
    sessdata = args.sessdata or os.environ.get('BILI_SESSDATA', '')
    bili_jct = args.bili_jct or os.environ.get('BILI_JCT', '')
    
    if cookie_str:
        # 从完整Cookie字符串解析
        try:
            cookies = {}
            for part in cookie_str.split(';'):
                part = part.strip()
                if '=' in part:
                    k, v = part.split('=', 1)
                    cookies[k.strip()] = v.strip()
            sessdata = cookies.get('SESSDATA', sessdata)
            bili_jct = cookies.get('bili_jct', bili_jct)
            buvid3 = cookies.get('buvid3', '')
            dedeuserid = cookies.get('DedeUserID', '')
            ac_time_value = cookies.get('ac_time_value', '')
        except Exception as e:
            print(f"  [警告] Cookie解析失败: {e}")
            sessdata, bili_jct = '', ''
    
    if sessdata:
        try:
            GLOBAL_CREDENTIAL = bili_credential(
                sessdata=sessdata,
                bili_jct=bili_jct,
            )
            print(f"  ✅ 已加载B站登录凭据（SESSDATA={'存在' if sessdata else '未设置'}）")
        except Exception as e:
            print(f"  [警告] 凭据创建失败: {e}，将以游客模式运行")
    else:
        print("  ⚠️  未提供登录Cookie，B站API会返回412错误")
        print("     安全方式（推荐）：将SESSDATA存入环境变量，不在命令行暴露")
        print("       export BILI_SESSDATA=你的SESSDATA值")
        print("       python3 bilibili_analyzer.py --mid 43683678")
        print("     或通过参数传入：")
        print("       python3 bilibili_analyzer.py --mid 43683678 --sessdata 你的SESSDATA值")
        print("")
        print("     获取SESSDATA: 浏览器登录B站→F12→Application→Cookies→bilibili.com→复制SESSDATA的值")

    # ==== 第一步：采集数据 ====
    videos, all_comments = collect_all_data(mid, pages=args.pages,
                                             limit_videos=args.limit_videos,
                                             sort=args.sort)

    if not all_comments:
        print("[提示] 未采集到评论数据")
        return

    # ==== 第二步：文本分析与NLP ====
    print(f"\n{'='*60}")
    print(f"  开始文本分析...")
    print(f"{'='*60}")

    # 情感分析
    print("  正在进行情感分析...")
    for c in all_comments:
        cleaned = preprocess_text(c.get('content', ''))
        score = sentiment_score(cleaned)
        c['sentiment'] = round(score, 4)
        c['sentiment_cat'] = classify_sentiment(score)

    sentiment_dist = dict(Counter(c['sentiment_cat'] for c in all_comments))

    # 分词 + 词频
    print("  正在进行分词与词频统计...")
    comment_texts = [preprocess_text(c.get('content', '')) for c in all_comments if c.get('content')]
    words = cut_words(comment_texts)
    word_freq = get_word_freq(words, topk=50)

    # 关键词提取
    print("  正在提取关键词...")
    keywords = extract_keywords(comment_texts, topk=30)

    # 热评排序
    top_hot = sorted(all_comments, key=lambda x: x.get('like', 0), reverse=True)

    # 时间信息转换
    for c in all_comments:
        if c.get('ctime'):
            c['ctime_str'] = datetime.fromtimestamp(c['ctime']).strftime('%Y-%m-%d %H:%M')
        else:
            c['ctime_str'] = ''

    # ==== 第三步：生成图表 ====
    print("  正在生成可视化图表...")
    images = {}

    wc_path = generate_wordcloud(word_freq)
    if wc_path:
        images['wordcloud'] = wc_path

    sentiment_chart = generate_sentiment_chart(
        [c['sentiment_cat'] for c in all_comments], output_dir)
    if sentiment_chart:
        images['sentiment'] = sentiment_chart

    df = pd.DataFrame(all_comments)
    trend_chart = generate_trend_chart(df, output_dir)
    if trend_chart:
        images['trend'] = trend_chart

    top_chart = generate_top_comments_chart(top_hot, output_dir)
    if top_chart:
        images['top_comments'] = top_chart

    # ==== 第四步：控制台输出 ====
    print_console_summary(videos, all_comments, sentiment_dist, keywords, word_freq, top_hot)

    # ==== 第五步：生成HTML报告 ====
    if not args.no_html:
        print("  正在生成HTML报告...")
        report_name = args.name or f"UP主{mid}评论分析报告"
        up_name = videos[0].get('author', str(mid)) if videos else str(mid)
        html_path = generate_html_report(up_name, mid, videos, all_comments,
                                          keywords, word_freq, sentiment_dist,
                                          top_hot, images, report_name)
        print(f"  ✅ HTML报告: {html_path}")

    # ==== 第六步：生成Excel ====
    if not args.no_excel:
        print("  正在生成Excel报表...")
        excel_path = write_excel(videos, all_comments, keywords, word_freq,
                                  sentiment_dist, output_dir)
        print(f"  ✅ Excel报表: {excel_path}")

    # ==== 保存完整JSON（备查） ====
    json_path = os.path.join(output_dir, 'raw_data.json')
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump({
            'videos': videos,
            'comments': all_comments,
            'keywords': keywords,
            'word_freq': word_freq,
            'sentiment_dist': sentiment_dist,
        }, f, ensure_ascii=False, indent=2)
    print(f"  ✅ 原始数据: {json_path}")

    print(f"\n{'='*60}")
    print(f"  ✅ 分析完成！所有文件保存在: {output_dir}")
    print(f"{'='*60}")
    print(f"  打开HTML报告: file://{os.path.abspath(html_path) if not args.no_html else '（已跳过）'}")


if __name__ == '__main__':
    main()
