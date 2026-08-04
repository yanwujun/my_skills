import React from "react";
import {
  AbsoluteFill,
  Audio,
  Img,
  Sequence,
  interpolate,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";
import {BGM, SEGMENTS, type Segment} from "./data";

const FONT_STACK =
  '"Noto Serif CJK SC", "Source Han Serif SC", "KaiTi", "STKaiti", serif';

export const PoemVideo: React.FC = () => {
  return (
    <AbsoluteFill style={{backgroundColor: "#0b0b10"}}>
      {SEGMENTS.map((seg, i) => (
        <Sequence key={"v" + i} from={seg.from} durationInFrames={seg.to - seg.from}>
          <SegmentView seg={seg} index={i} />
        </Sequence>
      ))}
      {SEGMENTS.map((seg, i) => (
        <Sequence key={"a" + i} from={seg.from} durationInFrames={seg.to - seg.from}>
          <SegmentAudio seg={seg} />
        </Sequence>
      ))}
      {BGM ? <Audio src={staticFile(BGM)} volume={0.14} loop /> : null}
    </AbsoluteFill>
  );
};

const SegmentAudio: React.FC<{seg: Segment}> = ({seg}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const dur = seg.to - seg.from;
  const vol = interpolate(
    frame,
    [0, fps * 0.35, dur - fps * 0.35, dur],
    [0, 1, 1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"}
  );
  return <Audio src={staticFile(seg.audio)} volume={vol} />;
};

const SegmentView: React.FC<{seg: Segment; index: number}> = ({seg, index}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const dur = seg.to - seg.from;
  const opacity = interpolate(
    frame,
    [0, fps * 0.7, dur - fps * 0.7, dur],
    [0, 1, 1, 0],
    {extrapolateLeft: "clamp", extrapolateRight: "clamp"}
  );
  const zoom = 1 + 0.06 * (frame / dur);
  const hue = (index * 47) % 360;
  return (
    <AbsoluteFill style={{opacity}}>
      {seg.image ? (
        <Img
          src={staticFile(seg.image)}
          style={{
            position: "absolute",
            width: "100%",
            height: "100%",
            objectFit: "cover",
            transform: `scale(${zoom})`,
          }}
        />
      ) : (
        <AbsoluteFill
          style={{
            background: `linear-gradient(160deg, hsl(${hue},38%,16%), hsl(${(hue + 40) % 360},45%,8%))`,
          }}
        />
      )}
      <AbsoluteFill
        style={{
          background:
            "radial-gradient(ellipse at center, rgba(0,0,0,0.15) 0%, rgba(0,0,0,0.62) 100%)",
        }}
      />
      <AbsoluteFill
        style={{
          justifyContent: "center",
          alignItems: "center",
          padding: 80,
        }}
      >
        <div
          style={{
            color: "#f5f0e8",
            fontFamily: FONT_STACK,
            fontSize: seg.fontSize,
            lineHeight: 1.7,
            letterSpacing: 4,
            textAlign: "center",
            whiteSpace: "pre-wrap",
            textShadow: "0 2px 24px rgba(0,0,0,0.85)",
            writingMode: seg.vertical ? "vertical-rl" : "horizontal-tb",
            maxHeight: "100%",
          }}
        >
          {seg.text}
        </div>
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
