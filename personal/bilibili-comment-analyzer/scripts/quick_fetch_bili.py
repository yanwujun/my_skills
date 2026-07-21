#!/usr/bin/env python3
"""
B站 UP主快速获取工具（轻量版）
=================================
无需登录，快速获取：用户信息 + 最新视频 + 热门评论

用法：
  python3 quick_fetch_bili.py --mid 1039025435
  python3 quick_fetch_bili.py --mid 1039025435 --videos 10 --comments 5

输出：
  控制台直接打印，适合在对话中使用
"""

import argparse, json, datetime, sys, os

# bilibili_api 必须安装在当前 Python 环境
# 如果报 ModuleNotFoundError，运行：python3 -m pip install bilibili-api-python
from bilibili_api import user, video, comment, sync


def fetch_user_info(mid: int) -> dict:
    """获取UP主基本信息"""
    u = user.User(mid)
    return sync(u.get_user_info())


def fetch_videos(mid: int, limit: int = 10) -> list:
    """获取UP主最新视频列表"""
    u = user.User(mid)
    result = sync(u.get_videos(ps=limit, pn=1))
    # vlist 可能在 result['list']['vlist'] 或 result['vlist']
    vlist = result.get('vlist', [])
    if not vlist and 'list' in result:
        vlist = result['list'].get('vlist', [])
    return vlist[:limit]


def fetch_comments(bvid: str, max_count: int = 8) -> list:
    """获取视频热门评论"""
    try:
        v = video.Video(bvid=bvid)
        info = sync(v.get_info())
        aid = info.get('aid', 0)
        
        cmt_page = sync(comment.get_comments(
            oid=aid,
            type_=comment.CommentResourceType.VIDEO,
            page_index=1,
            order=comment.OrderType.LIKE
        ))
        replies = cmt_page.get('replies') or []
        total = cmt_page.get('page', {}).get('acount', 0)
        
        result = []
        for r in replies[:max_count]:
            member = r.get('member', {})
            content_obj = r.get('content', {})
            entry = {
                'uname': member.get('uname', ''),
                'level': member.get('level_info', {}).get('current_level', 0),
                'message': content_obj.get('message', ''),
                'likes': r.get('like', 0),
                'rcount': r.get('rcount', 0),
            }
            # 楼层内回复（含UP主回复）
            sr_list = []
            sub_replies = r.get('replies') or []
            for sr in sub_replies[:3]:
                sr_member = sr.get('member', {})
                sr_content = sr.get('content', {})
                sr_list.append({
                    'uname': sr_member.get('uname', ''),
                    'mid': sr_member.get('mid', 0),
                    'message': sr_content.get('message', ''),
                })
            entry['sub_replies'] = sr_list
            result.append(entry)
        
        return {'total': total, 'comments': result, 'aid': aid}
    except Exception as e:
        return {'total': 0, 'comments': [], 'error': str(e)}


def main():
    parser = argparse.ArgumentParser(description='B站 UP主快速获取')
    parser.add_argument('--mid', type=int, required=True, help='UP主mid')
    parser.add_argument('--videos', type=int, default=10, help='展示视频数，默认10')
    parser.add_argument('--comments', type=int, default=8, help='每视频展示评论数，默认8')
    args = parser.parse_args()

    print(f"{'='*60}")
    print(f"B站 UP主快速获取")
    print(f"时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*60}")

    # 1. 用户信息
    print("\n--- UP主信息 ---")
    try:
        info = fetch_user_info(args.mid)
        print(f"昵称: {info.get('name', '')}")
        print(f"签名: {info.get('sign', '')}")
        print(f"等级: {info.get('level', '')}")
        print(f"性别: {info.get('sex', '')}")
        print(f"粉丝: {info.get('fans', '')}")
        print(f"关注: {info.get('friend', '')}")
        print(f"视频: {info.get('video_count', '')}")
        print(f"文章: {info.get('article_count', '')}")
    except Exception as e:
        print(f"获取失败: {e}")
        sys.exit(1)

    # 2. 视频列表
    print(f"\n--- 最新 {args.videos} 个视频 ---")
    try:
        videos = fetch_videos(args.mid, args.videos)
        for i, v in enumerate(videos, 1):
            ts = datetime.datetime.fromtimestamp(v.get('created', 0)).strftime('%Y-%m-%d')
            print(f"  {i:2d}. [{v.get('bvid','')}] {v.get('title','')}")
            print(f"      播放:{v.get('play',0)} 弹幕:{v.get('video_review',0)} 评论:{v.get('comment',0)} {ts}")
    except Exception as e:
        print(f"获取失败: {e}")
        sys.exit(1)

    # 3. 评论区（只取前5个视频）
    print(f"\n--- 评论区热评 ---")
    for v in videos[:5]:
        bvid = v.get('bvid', '')
        title = v.get('title', '')
        print(f"\n{'='*50}")
        print(f"【{title[:50]}】")
        print(f"BVID: {bvid}")
        
        result = fetch_comments(bvid, args.comments)
        total = result.get('total', 0)
        print(f"评论总数: {total}")
        
        for j, c in enumerate(result.get('comments', []), 1):
            print(f"  [{j}] {c['uname']} (Lv.{c['level']}) 👍{c['likes']}")
            print(f"       {c['message'][:300]}")
            for sr in c.get('sub_replies', []):
                tag = " 👑UP主" if sr.get('mid') == args.mid else ""
                print(f"     └─{sr['uname']}{tag}: {sr['message'][:200]}")
            print()

        if result.get('error'):
            print(f"  [错误] {result['error']}")

    print(f"\n{'='*60}")
    print("获取完成")
    print(f"{'='*60}")


if __name__ == '__main__':
    main()
