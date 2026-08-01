import {Composition} from "remotion";

import {ProductDemo} from "./compositions/ProductDemo";
import {VIDEO} from "./design/tokens";
import {BrandLandingScene} from "./scenes/BrandLandingScene";
import {SocialLabIntro} from "./scenes/SocialLabIntro";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="SocialLabIntro"
        component={SocialLabIntro}
        durationInFrames={120}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />

      <Composition
        id="BrandLandingScene"
        component={BrandLandingScene}
        durationInFrames={150}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />

      <Composition
        id="SocialLabProductDemo"
        component={ProductDemo}
        durationInFrames={270}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
    </>
  );
};