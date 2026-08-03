import { Composition } from "remotion";
import {
  MOBILE_VIDEO,
  MobileProductDemo,
} from "./compositions/MobileProductDemo";
import { ProductDemo } from "./compositions/ProductDemo";
import { ProductLaunchFilm } from "./compositions/ProductLaunchFilm";
import { LAUNCH_VIDEO } from "./design/launch-film-theme";
import { VIDEO } from "./design/tokens";
import { AgentMechanismScene } from "./scenes/AgentMechanismScene";
import { BrandLandingScene } from "./scenes/BrandLandingScene";
import { ConversationScene } from "./scenes/ConversationScene";
import { DynamicsScene } from "./scenes/DynamicsScene";
import { OutroScene } from "./scenes/OutroScene";
import { PersonSetupScene } from "./scenes/PersonSetupScene";
import { PersonaRevealScene } from "./scenes/PersonaRevealScene";
import { ReportOverviewScene } from "./scenes/ReportOverviewScene";
import { RewriteRetryScene } from "./scenes/RewriteRetryScene";
import { ScenarioFormScene } from "./scenes/ScenarioFormScene";
import { ScenarioPickerScene } from "./scenes/ScenarioPickerScene";
import { SocialLabIntro } from "./scenes/SocialLabIntro";
import { PRODUCT_FILM_DURATION, timeline } from "./timeline/product-film";

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
      {/* 发布宣传片：真实产品场景 + 广告化叙事层。 */}
      <Composition
        id="SocialLabProductFilm"
        component={ProductLaunchFilm}
        durationInFrames={PRODUCT_FILM_DURATION}
        fps={LAUNCH_VIDEO.fps}
        width={LAUNCH_VIDEO.width}
        height={LAUNCH_VIDEO.height}
      />
      <Composition
        id="SocialLabProductLaunchFilm"
        component={ProductLaunchFilm}
        durationInFrames={PRODUCT_FILM_DURATION}
        fps={LAUNCH_VIDEO.fps}
        width={LAUNCH_VIDEO.width}
        height={LAUNCH_VIDEO.height}
      />
      <Composition
        id="SocialLabProductFilmHD"
        component={ProductLaunchFilm}
        durationInFrames={PRODUCT_FILM_DURATION}
        fps={VIDEO.fps}
        width={1920}
        height={1080}
      />
      {/* 保留纯产品操作版，方便对照和后续迭代。 */}
      <Composition
        id="SocialLabProductDemo"
        component={ProductDemo}
        durationInFrames={PRODUCT_FILM_DURATION}
        fps={VIDEO.fps}
        width={VIDEO.width}
        height={VIDEO.height}
      />
      <Composition
        id="SocialLabProductMobile"
        component={MobileProductDemo}
        durationInFrames={PRODUCT_FILM_DURATION}
        fps={VIDEO.fps}
        width={MOBILE_VIDEO.width}
        height={MOBILE_VIDEO.height}
      />
    </>
  );
};
