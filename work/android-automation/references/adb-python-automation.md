# ADB + Python 安卓自动化 (PC 控制手机/模拟器)

适用: 无 root 手机或模拟器, 由电脑驱动 (无需装 APK 到手机); 是 AutoJs6 打包方案之外的轻量替代。
本项目实例: `~/douyin_fudai/douyin_fudai.py` (抢直播间福袋), OCR 冒烟测试通过 (置信度 0.95)。

## 连接与关键命令
- 模拟器 adb 端口: MuMu12=`127.0.0.1:16384`, 雷电=`5555`, 夜神=`62001`
- **WSL2 连不到 Windows 侧模拟器的 127.0.0.1** → 需模拟器开启"允许远程 ADB"后用 Windows IP 连接, 或脚本直接放 Windows 侧跑
- 截图: `adb exec-out screencap -p` — **二进制输出, subprocess 必须 binary 模式捕获** (text=True 会损坏)
- 点击: `adb shell input tap X Y`; 防锁屏: `adb shell svc power stayon true`
- UI 兜底: `adb shell uiautomator dump /sdcard/window_dump.xml` + `adb shell cat` 解析 XML 的 bounds
- 中文输入 (口令类任务): 装 ADBKeyboard app → `adb shell am broadcast -a ADB_INPUT_TEXT --es msg 文本` + `input keyevent 66` 发送

## Python 结构要点
- OCR: `rapidocr-onnxruntime` → `RapidOCR()(cv2_img)` 返回 `[[box4pts, text, score], ...]`; 直接吃 opencv ndarray (无需 PIL); 中文识别好, 离线
- 决策模型: 关键词分类 `join/joined/skip/fudai/verify`, 优先级 join > fudai; 已参与/粉丝团/充值/不满足 等必须排除
- 防误触: fudai 入口文本限短 (≤8 字符) 避免点中弹幕里含"福袋"的句子
- 节奏: 随机间隔 8-18s + 点击坐标抖动 ±10px; 截图失败重试; 每 5 分钟无目标才打日志 (防刷屏)
- **陷阱**: 抖音直播间 UI 自绘 → uiautomator dump 常为空, 必须以 OCR 为主, uiautomator 仅作兜底 (且只在 OCR 无结果时才 dump, 省资源)

## 环境
- platform-tools 下载: TUNA 镜像 `https://mirrors.tuna.tsinghua.edu.cn/Android/repository/platform-tools-latest-linux.zip` (dl.google 国内需代理); 脚本自动探测同目录 `platform-tools/adb`
- WSL 无 sudo 装不了 python3-venv (PEP 668) → 依赖已装的系统包直接 `python3` 跑

## 验证
渲染中文测试图 (PIL + `/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc`) → 跑脚本 OCR 函数 → 断言 best_target 命中目标文字。无设备也能验证整个识别/决策管线。
