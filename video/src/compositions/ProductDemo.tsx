import {
  AbsoluteFill,
  Sequence,
} from "remotion";

import {BrandLandingScene} from "../scenes/BrandLandingScene";
import {SocialLabIntro} from "../scenes/SocialLabIntro";

export const ProductDemo = () => {
  return (
    <AbsoluteFill>
      <Sequence
        from={0}
        durationInFrames={120}
        name="Scene 01 - Unsent Message"
      >
        <SocialLabIntro />
      </Sequence>

      <Sequence
        from={120}
        durationInFrames={150}
        name="Scene 02 - Brand Landing"
      >
        <BrandLandingScene />
      </Sequence>
    </AbsoluteFill>
  );
};