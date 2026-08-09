---
name: remotion-code-backgrounds
description: "Use when 新增 Remotion 代码背景风格/氛围元素。组件模式、验证法、实测踩坑手册。"
version: 1.0.0
---

# Remotion 代码绘制背景 · 元素开发指南

适用于任何用代码绘制背景的 Remotion 项目（散文诗视频 `~/poem-video` 模板、AI 周报等）。2026-08 实测新增 5 元素（雨滴涟漪/落叶/极光/萤火虫/蒲公英飘絮）+ 5 风格（autumn/aurora/fireflies/dandelion/summerbreeze），rain 增强涟漪。本文是"怎么加新元素不出坑"的开发手册。

## 触发条件

- 用户要求背景"更丰富/加氛围元素"（点菜式：雨滴涟漪、落叶、极光、萤火虫、蒲公英飘絮…）
- 需要给散文诗/文艺视频新增 `--bg-style` 代码背景风格
- 新元素渲染后看不到/太暗/不动，需要定位

## 接入流程（每加一个元素/风格走全这套）

1. `templates/poem-video/src/Video.tsx`：加组件（确定性伪随机，**禁 Math.random**）+ 在 `CodeBg` switch 加 `case "xxx"` 组装层叠
2. `scripts/poem_pipeline.py`：`--bg-style` choices 白名单 + help 文本（**漏了 argparse 报错**）
3. `SKILL.md` 背景风格表加一行
4. **同步工作副本**：`cp templates/poem-video/src/Video.tsx ~/poem-video/src/Video.tsx`
   ⚠️ pipeline 只在 `~/poem-video` **不存在**时才复制模板（`if not project.exists()`）；项目已存在时改模板必须手动 cp，否则渲染用旧组件（本会话踩过：改了模板没同步，渲染验证反复失败）
5. 验证：双帧差分（见下）→ 渲染 demo MP4
6. 预览产物 cp 到 `/mnt/d/平时处理文件/散文诗背景预览/`，交付 markdown 本地链接

## 组件模式（沿用现有约定）

```tsx
const seeded = (i: number, seed: number) => ((i * 137 + seed * 59) % 100) / 100;
const XS = Array.from({length: N}, (_, i) => ({
  x: seeded(i, S1) * 100, y0: seeded(i, S2) * 100, spd: ..., size: ..., o: ...,
}));
const Xs: React.FC = () => {
  const f = useCurrentFrame();   // Sequence 内自动为段内局部帧
  return (
    <AbsoluteFill style={{overflow: "hidden", pointerEvents: "none"}}>
      {XS.map((p, i) => <div key={i} style={{position:"absolute", left:`${x}%`, top:`${y}%`, ...}} />)}
    </AbsoluteFill>
  );
};
```

- 每字段独立 seed 号（S1/S2/S3...错开），避免元素排成一行
- 循环越界用模运算并加回负值范围：`((y0 + f*k*spd) % 110) - 5`、`(x + 105) % 105 - 2.5`
- CodeBg 层叠顺序（从底到顶）：渐变底 → 天景(云/星空/极光) → 光效(月/落日) → 剪影(山/树/草浪) → 粒子(雨/雪/叶/萤火/风丝) → 雾气 → 噪点
- **固定色调风格不随 hue 循环**：段 hue = (index*47)%360 会变，暖色主题（日暮）必须硬编码渐变，不要复用 FlowGradient 的 hue 参数

## 实测踩坑（每一条都付过代价）

### 1. SVG 散粒元素可能整组渲染为零像素（最坑）
落叶第一版 `<svg><path>`（绝对定位 + rotate + transformOrigin:center）**渲染成功但画面 0 像素**；隔离测试（单独 Composition 渲染同组件）正常 → 挂载环境兼容问题。**对策：粒子类元素一律用 div**。叶子 = `borderRadius: "50% 10% 50% 10%"` + linear-gradient 背景，观感接近。SVG 只用于大片形状（极光丝带、草浪整幅）。

### 2. 速度系数太小 = 元素堆在出生区
落叶 0.006 系数 30 秒才走 2% 屏高，全堆顶部。0.004 系数只适合 1-4px 小粒子（雪/微尘）；**大物体（叶子/飘絮）要 0.03-0.05**，出生范围撒开（`y0 = seeded*70 - 10` 而非 *30），保证任意帧画面都有分布。参考：落叶 0.04×spd(1.2-3)、蒲公英横漂 0.03、萤火虫 0.004（悬浮闪烁本应慢）。

### 3. 半透明元素像素探针永远测不到纯色阈值（验证方法的坑）
多层衰减：元素 alpha × 组件 opacity × 暗角 radial-gradient(0.15-0.62) → 白 alpha 0.9 的叶子实测 (128,64,32)，纯白阈值全灭。**这不是没渲染**。三版调参教训：别拿纯色阈值反复"验证"，用差分 + 用户看 demo 视频。

### 4. 波浪类相位混叠
草浪 `sin(x*freq*2π + f*speed + phase)`：speed 0.07 × 90 帧差 ≈ 2π 恰好同相 → 差分≈0 不代表不动（实际每秒 0.33Hz 在摆）。验证换帧差（45 帧）或避开整数周期。

### 5. 元素太暗/太细看不到
- 细线（蒲公英绒毛 1px）：加粗 1.6px + 末梢圆点 + 组件层 `filter: "drop-shadow(0 0 5px rgba(255,255,255,0.4))"`
- 风丝 alpha 0.12-0.16 不可见 → 0.34-0.44、高 6px、5 缕错开保证画面常有 1-2 缕
- 标准：**静态帧单看也能认出元素**，再谈氛围

### 6. 段级无背景风格标记
pipeline 段级标记只有【音色】【慢快沉轻亮】【rate/pitch】【音量】【停顿】【指令】，**没有 bg-style**——全片统一 `--bg-style`。别答应"按段换风格"（要改得动 pipeline 加标记支持）。

## 验证方法论（模型无视觉能力时）

vision_analyze 对纯文本回退模型报 `unknown variant image_url` 时，用 PIL 像素分析：
1. **双帧差分（首选）**：`npx remotion still poem --frame=A/B` 两帧 → 按 y 区域统计 `|ΔR|+|ΔG|+|ΔB|>25` 像素数 → 动态元素分布区必有 diff，静态背景（渐变/文字/剪影）≈0
2. **宽松色桶统计**：`r//16*16` 量化后 Counter 看显著色簇，别用窄阈值
3. ⚠️ 底部雾（Mist）+ 胶片噪点（Grain）是大面积动态源，会主导差分——分区域看增量
4. 差分比例参考（1080p，90 帧间隔）：元素明显 = 对应区域数千~数万 diff；云/雾高速层 = 十万级

## 演示与交付

- 用户要"看效果"：**直接 `remotion render` 出 MP4**（演示 6s/段×6 段=36s≈9.5MB），不要只给 still 静态图（用户会问"视频呢"）
- 成品放 `/mnt/d/项目/个人总结/散文诗视频/`，风格预览放 `/mnt/d/平时处理文件/散文诗背景预览/`，交付 markdown 本地链接
- **不主动推 QQ**（用户明确偏好；QQ 推送是框架协议审核报告专用）
- ⚠️ **CLI 终端 markdown 本地链接点不了**（用户实测反馈"播放点击不了"）：交付必须 **复制到桌面**（`/mnt/c/Users/Administrator/Desktop/<文件夹>/`）+ **给纯文本 Windows 路径**（`D:\...` 反斜杠格式，可直接贴资源管理器地址栏），不能只给 markdown 链接。用户说"打开文件/打开文件夹"时优先走桌面路径；interop 修复前 explorer.exe 调不起来（见 memory WSL interop 条目）
- 配音语气：正式出片默认 CosyVoice 角色化（用户明确不满 edge 默认音色），edge 仅快速试稿——见 prose-poetry-video skill 语气部分

## 相关

- 元素库/风格清单与散文诗出片流程：`prose-poetry-video`（user-owned，工作流主 skill）
- 周报视频（数据组件背景）：`ai-weekly-video`
