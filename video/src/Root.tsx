import {Composition} from "remotion";
import {SocialLabIntro} from "./scenes/SocialLabIntro";

export const RemotionRoot = () => {
  return (
    <>
      <Composition
        id="SocialLabIntro"
        component={SocialLabIntro}
        durationInFrames={150}
        fps={30}
        width={1920}
        height={1080}
      />
    </>
  );
};
