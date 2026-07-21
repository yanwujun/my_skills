// ─────────────────────────────────────────────
// AI 周报视频 — 可复用组件模板
// 复制到 Video.tsx 顶部，替换字幕数组和分镜即可
// ─────────────────────────────────────────────

import {
  AbsoluteFill, Audio, Sequence, useCurrentFrame,
  interpolate, spring, staticFile,
} from "remotion";
import React, { useMemo } from "react";

// ── Colors ──
const BG = "#09090f";
const ACCENT = "#00d4ff";
const ACCENT2 = "#a78bfa";
const ACCENT3 = "#f472b6";
const GREEN = "#4ade80";
const WHITE = "#e8e8ee";
const MUTED = "rgba(255,255,255,0.5)";
const CARD_BG = "rgba(255,255,255,0.04)";
const CARD_BORDER = "rgba(255,255,255,0.08)";

// ─────────────────────────────────────────────
// 基础背景组件
// ─────────────────────────────────────────────

const GradientBg: React.FC<{ c?: string }> = ({ c = ACCENT }) => {
  const f = useCurrentFrame();
  const d = interpolate(f, [0, 150], [0, 30], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ background: `radial-gradient(ellipse 80% 60% at ${50+d*0.3}% ${30-d*0.2}%, ${c}08 0%, transparent 60%),radial-gradient(ellipse 60% 50% at ${70-d*0.2}% ${70+d*0.3}%, ${c}05 0%, transparent 50%),${BG}` }} />;
};

const DotGrid: React.FC = () => {
  const f = useCurrentFrame();
  const op = interpolate(f, [0, 30], [0, 0.1], { extrapolateRight: "clamp" });
  return <AbsoluteFill style={{ opacity: op, pointerEvents: "none" }}><svg width="100%" height="100%"><defs><pattern id="dg" x="0" y="0" width="64" height="64" patternUnits="userSpaceOnUse"><circle cx="32" cy="32" r="1" fill="rgba(255,255,255,0.25)"/></pattern></defs><rect width="100%" height="100%" fill="url(#dg)"/></svg></AbsoluteFill>;
};

const Watermark: React.FC = () => (
  <div style={{ position: "absolute", bottom: 36, right: 48, fontSize: 20, color: "rgba(255,255,255,0.15)", zIndex: 20 }}>@无问凡</div>
);

const Particles: React.FC<{ count?: number; color?: string; seed?: number }> = ({ count = 20, color = ACCENT, seed = 0 }) => {
  const frame = useCurrentFrame();
  const particles = useMemo(() =>
    Array.from({ length: count }, (_, i) => ({
      x: ((i * 137 + seed * 59) % 100),
      y: ((i * 251 + seed * 43) % 100),
      size: ((i * 73 + seed * 17) % 3) + 1,
      speed: ((i * 47 + seed * 31) % 20) / 100 + 0.3,
      delay: (i * 33 + seed * 11) % 60,
      opacity: ((i * 89 + seed * 23) % 30) / 100 + 0.15,
    })), [count, seed]);
  return (
    <AbsoluteFill style={{ pointerEvents: "none", zIndex: 1 }}>
      {particles.map((p, i) => {
        const fy = (p.y + (frame * p.speed + p.delay) * 0.08) % 100;
        const fo = p.opacity + Math.sin(frame * 0.02 + i) * 0.1;
        return (
          <div key={i} style={{
            position: "absolute", left: `${p.x}%`, top: `${fy}%`,
            width: p.size * 2, height: p.size * 2, borderRadius: "50%",
            background: color, opacity: Math.max(0, fo),
            boxShadow: `0 0 ${p.size*4}px ${color}40`,
          }} />
        );
      })}
    </AbsoluteFill>
  );
};

const PulseRing: React.FC<{ color?: string }> = ({ color = ACCENT }) => {
  const f = useCurrentFrame();
  const s = 1 + (f % 120) * 0.008;
  const o = 1 - (f % 120) / 120;
  return (
    <AbsoluteFill style={{ pointerEvents: "none", justifyContent: "center", alignItems: "center", zIndex: 0 }}>
      <div style={{ width: 400, height: 400, borderRadius: "50%", border: `1px solid ${color}30`, transform: `scale(${s})`, opacity: o * 0.4 }} />
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────
// 字幕
// ─────────────────────────────────────────────

// 用法: 从 VTT 解析后粘贴替换这个数组
const SUBTITLES = [
  { from: 3, to: 99, text: "这周我翻 GitHub Trending 的时候，发现一个规律。" },
  // ... 粘贴 VTT 解析结果
];
const DURATION = 5088; // 最后一句的 to 帧数

const ActiveSub: React.FC = () => {
  const frame = useCurrentFrame();
  const sub = SUBTITLES.find((s) => frame >= s.from && frame < s.to);
  if (!sub) return null;
  const op = interpolate(frame, [sub.from, sub.from+4, sub.to-4, sub.to], [0,1,1,0], { extrapolateLeft: "clamp", extrapolateRight: "clamp" });
  return (
    <div style={{ position: "absolute", bottom: 100, left: "50%", transform: "translateX(-50%)", opacity: op, zIndex: 20 }}>
      <div style={{ background: "rgba(0,0,0,0.72)", backdropFilter: "blur(14px)", borderRadius: 14, padding: "14px 34px", maxWidth: "88vw", textAlign: "center", border: "1px solid rgba(255,255,255,0.06)" }}>
        <p style={{ color: WHITE, fontSize: 34, fontWeight: 500, margin: 0, lineHeight: 1.5 }}>{sub.text}</p>
      </div>
    </div>
  );
};

// ─────────────────────────────────────────────
// 业务组件
// ─────────────────────────────────────────────

const Chapter: React.FC<{ emoji: string; title: string; sub?: string }> = ({ emoji, title, sub }) => {
  const f = useCurrentFrame();
  const fi = spring({ frame: f, fps: 30, config: { damping: 18 } });
  const es = spring({ frame: f - 5, fps: 30, config: { damping: 12 } });
  const lw = interpolate(f, [10, 35], [0, 100], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <GradientBg /><DotGrid /><Particles seed={title.length} /><PulseRing />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", gap: 12 }}>
        <div style={{ fontSize: 72, opacity: fi, transform: `scale(${es})` }}>{emoji}</div>
        <h1 style={{ fontSize: 52, fontWeight: 700, color: WHITE, opacity: fi, margin: 0, letterSpacing: 2 }}>{title}</h1>
        {sub && <p style={{ fontSize: 26, color: ACCENT, marginTop: 0, opacity: fi }}>{sub}</p>}
        <div style={{ width: lw, height: 2, background: `linear-gradient(90deg,transparent,${ACCENT},transparent)`, borderRadius: 1 }} />
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const ProjCard: React.FC<{ emoji: string; name: string; stars: string; growth: string; desc: string; color?: string }> = ({ emoji, name, stars, growth, desc, color = ACCENT }) => {
  const f = useCurrentFrame();
  const si = spring({ frame: f, fps: 30, config: { damping: 20 } });
  const op = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const bw = interpolate(f, [10, 45], [0, 300], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <GradientBg c={color} /><DotGrid /><Particles color={color} seed={name.length} /><PulseRing color={color} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 80 }}>
        <div style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 24, padding: "40px 56px", maxWidth: 900, width: "100%", transform: `translateX(${(1-si)*60}px)`, boxShadow: `0 0 60px ${color}08` }}>
          <div style={{ display: "flex", alignItems: "center", gap: 20, marginBottom: 20 }}>
            <div style={{ fontSize: 44, width: 72, height: 72, borderRadius: 18, background: `${color}15`, display: "flex", alignItems: "center", justifyContent: "center" }}>{emoji}</div>
            <div>
              <h2 style={{ fontSize: 38, fontWeight: 700, color: WHITE, margin: 0 }}>{name}</h2>
              <div style={{ display: "flex", gap: 16, marginTop: 4 }}>
                <span style={{ fontSize: 20, color, fontWeight: 600 }}>⭐ {stars}</span>
                <span style={{ fontSize: 20, color: growth.startsWith("+") ? GREEN : MUTED }}>{growth}</span>
              </div>
            </div>
          </div>
          <p style={{ fontSize: 22, color: MUTED, margin: 0, lineHeight: 1.6 }}>{desc}</p>
          <div style={{ marginTop: 20, height: 3, background: `${color}30`, borderRadius: 2, overflow: "hidden" }}>
            <div style={{ width: bw, height: "100%", background: color, borderRadius: 2 }} />
          </div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const NumberCards: React.FC<{ items: { v: string; l: string; c?: string }[] }> = ({ items }) => {
  const f = useCurrentFrame();
  const cs = [ACCENT, ACCENT2, ACCENT3, ACCENT];
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <GradientBg /><DotGrid /><Particles /><PulseRing />
      <div style={{ display: "flex", gap: 36 }}>
        {items.map((it, i) => {
          const s = spring({ frame: f - i*8, fps: 30, config: { damping: 15 } });
          const c = it.c || cs[i%cs.length];
          return (
            <div key={i} style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 18, padding: "28px 40px", textAlign: "center", transform: `scale(${s})`, boxShadow: `0 0 40px ${c}06` }}>
              <div style={{ fontSize: 48, fontWeight: 800, color: c, marginBottom: 2 }}>{it.v}</div>
              <div style={{ fontSize: 18, color: MUTED }}>{it.l}</div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const BarChart: React.FC<{ bars: { l: string; v: number; c?: string }[] }> = ({ bars }) => {
  const f = useCurrentFrame();
  const max = Math.max(...bars.map(b=>b.v));
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <GradientBg /><DotGrid /><Particles /><PulseRing />
      <div style={{ maxWidth: 860, width: "100%", padding: 60 }}>
        <h3 style={{ fontSize: 26, color: MUTED, marginBottom: 36, fontWeight: 500, textAlign: "center" }}>28 天 Star 增量 TOP 5</h3>
        {bars.map((b,i) => {
          const delay = f - i*12;
          const w = spring({ frame: delay>0?delay:0, fps:30, config:{damping:18} });
          const c = b.c || ACCENT;
          const highlight = f >= delay+40 && b.v === max;
          return (
            <div key={i} style={{ marginBottom: 22 }}>
              <div style={{ display:"flex", justifyContent:"space-between", marginBottom:8, fontSize:20 }}>
                <span style={{ color:WHITE }}>{b.l}</span>
                <span style={{ color:c, fontWeight:600 }}>+{b.v}⭐</span>
              </div>
              <div style={{ height:highlight?14:10, background:`${c}20`, borderRadius:5, overflow:"hidden" }}>
                <div style={{ width:`${(b.v/max)*100*w}%`, height:"100%", background:c, borderRadius:5, boxShadow:highlight?`0 0 12px ${c}60`:undefined }} />
              </div>
            </div>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

const FactSlide: React.FC<{ text: string; color?: string }> = ({ text, color = ACCENT }) => {
  const f = useCurrentFrame();
  const s = spring({ frame: f, fps: 30, config: { damping: 15 } });
  return (
    <AbsoluteFill>
      <GradientBg c={color} /><DotGrid /><Particles color={color} seed={text.length} /><PulseRing color={color} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center", padding: 100 }}>
        <div style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 20, padding: "36px 56px", maxWidth: 900, transform: `scale(${s})`, boxShadow: `0 0 60px ${color}08` }}>
          <p style={{ fontSize: 34, color: WHITE, margin: 0, textAlign: "center", lineHeight: 1.6 }}>{text}</p>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const HighlightCard: React.FC<{ emoji: string; title: string; detail?: string; color?: string; accent2?: string }> = ({ emoji, title, detail, color = ACCENT3, accent2 }) => {
  const f = useCurrentFrame();
  const s = spring({ frame: f, fps: 30, config: { damping: 15 } });
  const op = interpolate(f, [0, 10], [0, 1], { extrapolateRight: "clamp" });
  const glow = Math.sin(f * 0.05) * 0.3 + 0.5;
  return (
    <AbsoluteFill style={{ opacity: op }}>
      <GradientBg c={color} /><DotGrid /><Particles color={color} seed={title.length} count={30} />
      <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
        <div style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 24, padding: "48px 64px", maxWidth: 860, width: "100%", textAlign: "center", transform: `scale(${s})`, boxShadow: `0 0 ${80*glow}px ${color}${Math.round(glow*20).toString(16)}`, position:"relative", overflow:"hidden" }}>
          <div style={{ position:"absolute", top:-80, right:-80, width:200, height:200, borderRadius:"50%", background:`${color}08`, pointerEvents:"none" }} />
          <div style={{ fontSize: 64, marginBottom: 12 }}>{emoji}</div>
          <h2 style={{ fontSize: 44, fontWeight: 800, color: WHITE, margin: 0 }}>{title}</h2>
          {detail && <p style={{ fontSize: 30, color: accent2||color, marginTop: 12, fontWeight: 600 }}>{detail}</p>}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const CategoryBreakdown: React.FC = () => {
  const cats = [
    { l: "AI Agent 框架", v: 12, c: ACCENT },
    { l: "开发工具 / MCP", v: 9, c: ACCENT2 },
    { l: "LLM 工具 / 平台", v: 5, c: ACCENT3 },
    { l: "多模态 / 应用", v: 4, c: GREEN },
  ];
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <GradientBg /><DotGrid /><Particles /><PulseRing />
      <div style={{ maxWidth: 860, width: "100%", padding: 60 }}>
        <h3 style={{ fontSize: 24, color: MUTED, marginBottom: 32, fontWeight: 500, textAlign: "center" }}>本周 30 个项目 · 7 大类别</h3>
        <div style={{ display: "flex", justifyContent: "center", gap: 20, flexWrap: "wrap" }}>
          {cats.map((c, i) => {
            const delay = f - i * 12;
            const s = spring({ frame: delay > 0 ? delay : 0, fps: 30, config: { damping: 15 } });
            return (
              <div key={i} style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 16, padding: "20px 28px", textAlign: "center", transform: `scale(${s})`, minWidth: 160 }}>
                <div style={{ fontSize: 40, fontWeight: 800, color: c.c }}>{c.v}</div>
                <div style={{ fontSize: 16, color: MUTED, marginTop: 4 }}>{c.l}</div>
              </div>
            );
          })}
        </div>
      </div>
    </AbsoluteFill>
  );
};

const SideBySide: React.FC<{
  left: { emoji: string; name: string; stars: string; c?: string };
  right: { emoji: string; name: string; stars: string; c?: string };
  vs: string;
}> = ({ left, right, vs }) => {
  const f = useCurrentFrame();
  const ls = spring({ frame: f, fps: 30, config: { damping: 18 } });
  const rs = spring({ frame: f - 8, fps: 30, config: { damping: 18 } });
  const midW = interpolate(f, [20, 50], [0, 60], { extrapolateRight: "clamp" });
  return (
    <AbsoluteFill>
      <GradientBg /><DotGrid /><Particles /><PulseRing />
      <AbsoluteFill style={{ flexDirection: "row", justifyContent: "center", alignItems: "center", gap: 0 }}>
        <div style={{ transform: `scale(${ls})`, background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 20, padding: "32px 40px", textAlign: "center" }}>
          <div style={{ fontSize: 48 }}>{left.emoji}</div>
          <h3 style={{ fontSize: 28, color: WHITE, margin: "8px 0" }}>{left.name}</h3>
          <div style={{ fontSize: 22, color: left.c||ACCENT, fontWeight: 600 }}>⭐ {left.stars}</div>
        </div>
        <div style={{ width: midW, textAlign: "center", overflow: "hidden" }}>
          <span style={{ fontSize: 36, color: ACCENT, fontWeight: 700 }}>{vs}</span>
        </div>
        <div style={{ transform: `scale(${rs})`, background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 20, padding: "32px 40px", textAlign: "center" }}>
          <div style={{ fontSize: 48 }}>{right.emoji}</div>
          <h3 style={{ fontSize: 28, color: WHITE, margin: "8px 0" }}>{right.name}</h3>
          <div style={{ fontSize: 22, color: right.c||ACCENT2, fontWeight: 600 }}>⭐ {right.stars}</div>
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};

const FlowPipeline: React.FC<{ steps: string[] }> = ({ steps }) => {
  const f = useCurrentFrame();
  return (
    <AbsoluteFill style={{ justifyContent: "center", alignItems: "center" }}>
      <GradientBg c={ACCENT3} /><DotGrid /><Particles color={ACCENT3} seed={99} /><PulseRing color={ACCENT3} />
      <div style={{ display: "flex", alignItems: "center", gap: 4, flexWrap: "wrap", justifyContent: "center", maxWidth: 1000 }}>
        {steps.map((step, i) => {
          const s = spring({ frame: f - i*10, fps: 30, config: { damping: 16 } });
          return (
            <React.Fragment key={i}>
              <div style={{ background: CARD_BG, border: `1px solid ${CARD_BORDER}`, borderRadius: 12, padding: "14px 24px", fontSize: 20, color: WHITE, transform: `scale(${s})`, whiteSpace: "nowrap" }}>{step}</div>
              {i < steps.length-1 && <span style={{ color: ACCENT3, fontSize: 20, transform: `scale(${spring({frame:f-i*10-5,fps:30,config:{damping:16}})}` }}>→</span>}
            </React.Fragment>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

// ─────────────────────────────────────────────
// 主 Composition（替换字幕 + 分镜）
// ─────────────────────────────────────────────

export const AIWeeklyVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{ backgroundColor: BG, fontFamily: "sans-serif" }}>
      <Audio src={staticFile("narration_YYYYMMDD.mp3")} />
      <Sequence from={0} durationInFrames={DURATION}><ActiveSub /></Sequence>
      <Sequence from={0} durationInFrames={DURATION}><Watermark /></Sequence>

      {/* 粘贴分镜 Sequence */}

    </AbsoluteFill>
  );
};
