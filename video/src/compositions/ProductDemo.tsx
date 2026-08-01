import {AbsoluteFill, Sequence} from "remotion";

import {BrandLandingScene} from "../scenes/BrandLandingScene";
import {ScenarioFormScene} from "../scenes/ScenarioFormScene";
import {ScenarioPickerScene} from "../scenes/ScenarioPickerScene";
import {SocialLabIntro} from "../scenes/SocialLabIntro";

export const ProductDemo = () => {
  return (
    <AbsoluteFill>
      <Sequence
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

      <Sequence
        from={270}
        durationInFrames={180}
        name="Scene 03 - Scenario Picker"
      >
        <ScenarioPickerScene />
      </Sequence>

      <Sequence
        from={450}
        durationInFrames={240}
        name="Scene 04 - Scenario Form"
      >
        <ScenarioFormScene />
      </Sequence>
    </AbsoluteFill>
  );
};
