import {AbsoluteFill, Sequence} from "remotion";

import {
  ProductAudioTrack,
  type ProductAudioTrackProps,
} from "../audio/ProductAudioTrack";
import {
  ProductBgmTrack,
  type ProductBgmTrackProps,
} from "../audio/ProductBgmTrack";
import {AgentMechanismScene} from "../scenes/AgentMechanismScene";
import {BrandLandingScene} from "../scenes/BrandLandingScene";
import {ConversationScene} from "../scenes/ConversationScene";
import {DynamicsScene} from "../scenes/DynamicsScene";
import {OutroScene} from "../scenes/OutroScene";
import {PersonSetupScene} from "../scenes/PersonSetupScene";
import {PersonaRevealScene} from "../scenes/PersonaRevealScene";
import {ReportOverviewScene} from "../scenes/ReportOverviewScene";
import {RewriteRetryScene} from "../scenes/RewriteRetryScene";
import {ScenarioFormScene} from "../scenes/ScenarioFormScene";
import {ScenarioPickerScene} from "../scenes/ScenarioPickerScene";
import {SocialLabIntro} from "../scenes/SocialLabIntro";
import {timeline} from "../timeline/product-film";

const SCENE_PREMOUNT_FRAMES = 12;

export type ProductDemoProps = Readonly<{
  audio?: ProductAudioTrackProps["settings"];
  bgm?: ProductBgmTrackProps["settings"];
}>;



export const ProductDemo = ({audio, bgm}: ProductDemoProps) => {
  return (
    <AbsoluteFill>
      <Sequence
        durationInFrames={timeline.unsent.duration}
        name="Scene 01 - Unsent Message"
      >
        <SocialLabIntro />
      </Sequence>

      <Sequence
        from={timeline.landing.from}
        durationInFrames={timeline.landing.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 02 - Brand Landing"
      >
        <BrandLandingScene />
      </Sequence>

      <Sequence
        from={timeline.picker.from}
        durationInFrames={timeline.picker.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 03 - Scenario Picker"
      >
        <ScenarioPickerScene />
      </Sequence>

      <Sequence
        from={timeline.scenarioForm.from}
        durationInFrames={timeline.scenarioForm.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 04 - Scenario Form"
      >
        <ScenarioFormScene />
      </Sequence>

      <Sequence
        from={timeline.personSetup.from}
        durationInFrames={timeline.personSetup.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 05 - Person Setup"
      >
        <PersonSetupScene />
      </Sequence>

      <Sequence
        from={timeline.persona.from}
        durationInFrames={timeline.persona.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 06 - Persona Reveal"
      >
        <PersonaRevealScene />
      </Sequence>

      <Sequence
        from={timeline.conversation.from}
        durationInFrames={timeline.conversation.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 07 - Conversation"
      >
        <ConversationScene />
      </Sequence>

      <Sequence
        from={timeline.mechanism.from}
        durationInFrames={timeline.mechanism.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 08 - Agent Mechanism"
      >
        <AgentMechanismScene />
      </Sequence>

      <Sequence
        from={timeline.dynamics.from}
        durationInFrames={timeline.dynamics.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 09 - Dynamics"
      >
        <DynamicsScene />
      </Sequence>

      <Sequence
        from={timeline.report.from}
        durationInFrames={timeline.report.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 10 - Report Overview"
      >
        <ReportOverviewScene />
      </Sequence>

      <Sequence
        from={timeline.rewrite.from}
        durationInFrames={timeline.rewrite.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 11 - Rewrite and Retry"
      >
        <RewriteRetryScene />
      </Sequence>

      <Sequence
        from={timeline.outro.from}
        durationInFrames={timeline.outro.duration}
        premountFor={SCENE_PREMOUNT_FRAMES}
        name="Scene 12 - Outro"
      >
        <OutroScene />
      </Sequence>

      <ProductBgmTrack settings={bgm} />
      <ProductAudioTrack settings={audio} />
    </AbsoluteFill>
  );
};
