import {Composition} from "remotion";

import {ProductDemo} from "./compositions/ProductDemo";
import {VIDEO} from "./design/tokens";
import {BrandLandingScene} from "./scenes/BrandLandingScene";
import {ScenarioFormScene} from "./scenes/ScenarioFormScene";
import {ScenarioPickerScene} from "./scenes/ScenarioPickerScene";
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
        id="ScenarioPickerScene"
        component={ScenarioPickerScene}
        durationInFrames={180}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />

      <Composition
        id="ScenarioFormScene"
        component={ScenarioFormScene}
        durationInFrames={240}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />

      <Composition
        id="SocialLabProductDemo"
        component={ProductDemo}
        durationInFrames={690}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
    </>
  );
};
