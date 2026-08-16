---
name: android-automation
description: Use when 安卓自动化, AutoJs6脚本, ADB控制, APK打包. 双方案+打包修复+签名+反监测边界。
version: 1.0.0
author: hermes-curator
license: CC-BY-4.0
metadata:
  hermes:
    tags: [android, autojs, adb, apk, automation, ocr]
    related_skills: [wsl-development, wsl-hybrid-agent-tools]
---

# 安卓手机自动化 (AutoJs6 / ADB / APK 打包)

## When to Use (触发条件)
- 用户要"手机自动化 / 挂机 / 抢X领X / 打包成 APK / 反监测"
- 需要控制安卓 app 界面 (截图识别 + 模拟点击), 典型如抖音福袋/直播间自动化

## 方案决策
| 需求 | 方案 |
|---|---|
| 手机独立运行、要 APK 安装包 | **AutoJs6** (无障碍服务, 可打包独立 APK) |
| PC 控制手机/模拟器, 不需要装手机 | **Python + ADB + RapidOCR** |
| 屏幕文字识别 (OCR) | 两者都有: AutoJs6 paddle 模式 / rapidocr-onnxruntime |

## 方案一: AutoJs6 手机端 (可打包 APK)
1. 项目结构: `autojs/` 目录 + `project.json` (`name`/`packageName`/`main`/`icon`) + 主脚本 + `icon.png`
2. 核心 API (6.x, 文档 docs.autojs6.com):
   - 权限: `auto.waitFor()` 无障碍; `images.requestScreenCapture()` + `images.captureScreen()` 截图
   - OCR: `ocr.mode = "paddle"` ← **国内手机必设** (mlkit 模式需 Google 服务); `ocr.detect(img)` → `[{text, confidence, bounds}]`, bounds 有 `centerX()/centerY()`
   - 动作: `click(x,y)`, `swipe(x1,y1,x2,y2,ms)`, `back()`, `sleep(ms)`
3. 打包: 见 `references/autojs6-apk-packaging.md` (⚠️ 含工具 bug 修复, 不可跳过)

## 方案二: ADB + Python (PC 控制)
- 截图 `adb exec-out screencap -p` (二进制模式捕获), 点击 `adb shell input tap`, 防锁屏 `adb shell svc power stayon true`
- OCR: rapidocr-onnxruntime (中文好、离线); uiautomator dump 兜底
- 细节与陷阱: `references/adb-python-automation.md`

## 反监测设计 (用户要求"反监测"时)
**做 — 行为自然化**: 随机轮询间隔、点击坐标抖动、随机跳过部分目标、参与冷却、定时随机休息、非高峰时段休眠、偶发真人动作 (轻滑/开评论区)、检测到人机验证立即暂停并提醒人工。
**不做 — 对抗性隐蔽**: 隐藏无障碍/框架痕迹、伪造设备指纹、注入篡改 app。明说边界: ① 平台风控核心是账号权重+行为模式, 隐藏框架收益有限; ② 被识破处罚更重 (永久封号); ③ 属规避平台安全措施。同时给账号层建议 (小号/先养号/限时挂机)。

## 通用陷阱
- **autojs6-apkbuilder v1.1.0 会丢 `lib/` 与 OCR 模型资产** → 必须从模板补回 + 重新签名, 否则 APK 装上即崩 (详见 reference)
- 打包需 Java 17 (WSL 无 sudo 时装便携 JDK 到 home) + AutoJs6 APK 模板 (arm64 版, ~139MB)
- Node CLI 是 `java -jar` 的包装: 系统无 Java 时**必须 `export JAVA_HOME`**, 否则 find-java-home 报 ERR_INVALID_ARG_TYPE
- **签名密钥 keystore 必须随交付保留**: 升级 APK 用同一密钥, 否则无法覆盖安装
- 改脚本后重打包用一键脚本 (见 reference 的 build_apk.sh 模式)

## 验证实践 (交付前必做)
1. OCR 冒烟: PIL + 中文字体 (wqy-zenhei.ttc) 渲染含目标文字的图 → 跑识别 → 断言命中 (见 scripts/)
2. APK 结构: zipfile 检查 `lib/`、`assets/models/`、`assets/mlkit-google-ocr-models/`、脚本已加密 (无明文)
3. 签名: uber-apk-signer 输出 `signature verified [v2, v3]`

## 支持文件
- `references/autojs6-apk-packaging.md` — 打包全流程 + 工具 bug 修复 + 签名 + GitHub Actions
- `references/adb-python-automation.md` — ADB+Python 方案细节、模拟器端口、ADBKeyboard
- `scripts/fix_apk_missing_assets.py` — 打包后补回丢失资产的修复脚本 (可直接运行)

## 边界
个人自动化用途 (抢福袋等) 属灰色地带, 交付时给出风险提示 (封号风险、小号建议、平台规则), 不做对抗性隐蔽手段。
