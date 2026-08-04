import React from "react";
import {Composition} from "remotion";
import {PoemVideo} from "./Video";
import {FPS, HEIGHT, TOTAL_FRAMES, WIDTH} from "./data";

export const RemotionRoot: React.FC = () => {
  return (
    <Composition
      id="poem"
      component={PoemVideo}
      durationInFrames={TOTAL_FRAMES}
      fps={FPS}
      width={WIDTH}
      height={HEIGHT}
    />
  );
};
