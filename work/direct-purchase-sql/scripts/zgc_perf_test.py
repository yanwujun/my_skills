#!/usr/bin/env python3
"""中关村回调接口性能测试脚本。

用法: python3 zgc_perf_test.py [可选: 迭代次数]

需要: Python 3.6+ (stdlib only, no deps)
环境: WSL 下可直接运行

示例:
    python3 zgc_perf_test.py          # 默认 10 次
    python3 zgc_perf_test.py 20       # 20 次
    python3 zgc_perf_test.py 5 显示器  # 5 次，用显示器目录
"""

import urllib.request, base64, ssl, json, time, uuid, sys

TOKEN_URL = "https://www.xcjshow1.gm/djc-gateway/authing/oauth/token"
AUTH_B64 = base64.b64encode(b"zcsc_zdzs:123456").decode()
CALLBACK_URL = (
    "https://www.xcjshow1.gm/xcj-gateway/api/v2/xcjmallbase/v1/public"
    "/zdzs/callback/product-audit-result?__platDomain__=zc-mall.xcjshow1.gm"
)
IMAGE_URL = "https://www.xcjshow1.gm/group1/M00/30/A2/OBS_161b52a5ce823000.png"
CTX = ssl._create_unverified_context()


def get_token():
    req = urllib.request.Request(TOKEN_URL, method="POST")
    req.add_header("Authorization", f"Basic {AUTH_B64}")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    resp = urllib.request.urlopen(req, data=b"grant_type=client_credentials", context=CTX)
    return json.loads(resp.read())["access_token"]


def make_body(idx, stock_dir="台式计算机", params=None):
    if params is None:
        params = {"CPU型号": "Intel i7-13700", "操作系统": "Windows 11", "内存容量": "16GB"}
    uid = f"perf-{uuid.uuid4().hex[:8]}"
    return json.dumps({
        "zdSpu": uid,
        "goodsNo": f"151||{uid}",
        "state": 2,
        "goodsName": f"性能测试商品 #{idx}",
        "brandName": "联想",
        "stockDirName": stock_dir,
        "model": f"BENCH-{idx:03d}",
        "unit": "台",
        "exPrice": 5000.00,
        "gtin": "6901234567890",
        "gtinImgUrl": IMAGE_URL,
        "images": [IMAGE_URL],
        "params": json.dumps(params),
    }).encode("utf-8")


def main():
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    stock_dir = sys.argv[2] if len(sys.argv) > 2 else "台式计算机"

    token = get_token()
    print(f"Token: ...{token[-10:]}")
    print(f"目录: {stock_dir}, 迭代: {n} 次\n")

    # Warmup
    req = urllib.request.Request(CALLBACK_URL, method="POST", data=make_body(0, stock_dir))
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Content-Type", "application/json")
    t0 = time.perf_counter()
    urllib.request.urlopen(req, context=CTX, timeout=30)
    print(f"Warmup: {time.perf_counter() - t0:.2f}s\n")

    # Benchmark
    results = []
    for i in range(1, n + 1):
        body = make_body(i, stock_dir)
        req = urllib.request.Request(CALLBACK_URL, method="POST", data=body)
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")

        t0 = time.perf_counter()
        try:
            resp = urllib.request.urlopen(req, context=CTX, timeout=60)
            elapsed = time.perf_counter() - t0
            rbody = json.loads(resp.read().decode())
            results.append(elapsed)
            print(f"  #{i:2d}: {elapsed:.2f}s  HTTP 200  {rbody.get('msg', '?')}")
        except urllib.error.HTTPError as e:
            elapsed = time.perf_counter() - t0
            err = e.read().decode("utf-8", errors="replace")[:120]
            print(f"  #{i:2d}: {elapsed:.2f}s  HTTP {e.code}  {err}")
        except Exception as e:
            elapsed = time.perf_counter() - t0
            print(f"  #{i:2d}: {elapsed:.2f}s  ERROR: {e}")

    if results:
        sorted_t = sorted(results)
        print(f"\n{'='*50}")
        print(f"{len(results)}/{n} 成功")
        print(f"  Min:     {sorted_t[0]:.2f}s")
        print(f"  Max:     {sorted_t[-1]:.2f}s")
        print(f"  Avg:     {sum(results)/len(results):.2f}s")
        print(f"  Median:  {sorted_t[len(sorted_t)//2]:.2f}s")
        if len(sorted_t) >= 10:
            print(f"  P90:     {sorted_t[int(len(sorted_t)*0.9)]:.2f}s")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
