import {Composition} from "remotion";

import {ProductDemo} from "./compositions/ProductDemo";
import {VIDEO} from "./design/tokens";
import {AgentMechanismScene} from "./scenes/AgentMechanismScene";
import {BrandLandingScene} from "./scenes/BrandLandingScene";
import {ConversationScene} from "./scenes/ConversationScene";
import {DynamicsScene} from "./scenes/DynamicsScene";
import {OutroScene} from "./scenes/OutroScene";
import {PersonSetupScene} from "./scenes/PersonSetupScene";
import {PersonaRevealScene} from "./scenes/PersonaRevealScene";
import {ReportOverviewScene} from "./scenes/ReportOverviewScene";
import {RewriteRetryScene} from "./scenes/RewriteRetryScene";
import {ScenarioFormScene} from "./scenes/ScenarioFormScene";
import {ScenarioPickerScene} from "./scenes/ScenarioPickerScene";
import {SocialLabIntro} from "./scenes/SocialLabIntro";
import {PRODUCT_FILM_DURATION, timeline} from "./timeline/product-film";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="SocialLabIntro"
        component={SocialLabIntro}
        durationInFrames={timeline.unsent.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="BrandLandingScene"
        component={BrandLandingScene}
        durationInFrames={timeline.landing.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="ScenarioPickerScene"
        component={ScenarioPickerScene}
        durationInFrames={timeline.picker.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="ScenarioFormScene"
        component={ScenarioFormScene}
        durationInFrames={timeline.scenarioForm.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="PersonSetupScene"
        component={PersonSetupScene}
        durationInFrames={timeline.personSetup.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="PersonaRevealScene"
        component={PersonaRevealScene}
        durationInFrames={timeline.persona.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="ConversationScene"
        component={ConversationScene}
        durationInFrames={timeline.conversation.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="AgentMechanismScene"
        component={AgentMechanismScene}
        durationInFrames={timeline.mechanism.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="DynamicsScene"
        component={DynamicsScene}
        durationInFrames={timeline.dynamics.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="ReportOverviewScene"
        component={ReportOverviewScene}
        durationInFrames={timeline.report.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="RewriteRetryScene"
        component={RewriteRetryScene}
        durationInFrames={timeline.rewrite.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="OutroScene"
        component={OutroScene}
        durationInFrames={timeline.outro.duration}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />

      <Composition
        id="SocialLabProductFilm"
        component={ProductDemo}
        durationInFrames={PRODUCT_FILM_DURATION}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="SocialLabProductDemo"
        component={ProductDemo}
        durationInFrames={PRODUCT_FILM_DURATION}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
    </>
  );
};
