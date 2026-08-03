import {
  AbsoluteFill,
  Easing,
  interpolate,
  spring,
  useCurrentFrame,
  useVideoConfig,
} from "remotion";

import {
  LaunchAccentTrack,
  type LaunchAccentTrackSettings,
} from "../audio/LaunchAccentTrack";
import {
  ProductAudioTrack,
  type ProductAudioTrackProps,
} from "../audio/ProductAudioTrack";
import {
  ProductBgmTrack,
  type ProductBgmTrackProps,
} from "../audio/ProductBgmTrack";
import {LAUNCH_FILM} from "../design/launch-film-theme";
import {VIDEO} from "../design/tokens";
import {
  PRODUCT_FILM_DURATION,
  timeline,
} from "../timeline/product-film";
import {ProductDemo} from "./ProductDemo";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const EASE_OUT = Easing.bezier(0.16, 1, 0.3, 1);

type ProductSceneKey = keyof typeof timeline;

const SCENE_ORDER = Object.keys(timeline) as ProductSceneKey[];

type StageConfig = Readonly<{
  scale: number;
  x: number;
  y: number;
  radius: number;
  shadowOpacity: number;
  dim: number;
}>;

const STAGE_CONFIGS: Record<ProductSceneKey, StageConfig> = {
  unsent: {
    scale: 1,
    x: 0,
    y: 0,
    radius: 0,
    shadowOpacity: 0,
    dim: 0,
  },
  landing: {
    scale: 1,
    x: 0,
    y: 0,
    radius: 0,
    shadowOpacity: 0,
    dim: 0,
  },
  picker: {
    scale: 0.78,
    x: 210,
    y: 10,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  scenarioForm: {
    scale: 0.77,
    x: 214,
    y: 8,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  personSetup: {
    scale: 0.77,
    x: -205,
    y: 8,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  persona: {
    scale: 0.82,
    x: 172,
    y: 2,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  conversation: {
    scale: 0.82,
    x: -172,
    y: 2,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  mechanism: {
    scale: 0.82,
    x: 0,
    y: 76,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  dynamics: {
    scale: 0.8,
    x: 190,
    y: 8,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  report: {
    scale: 0.8,
    x: -190,
    y: 8,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  rewrite: {
    scale: 0.74,
    x: 250,
    y: 20,
    radius: 30,
    shadowOpacity: 1,
    dim: 0,
  },
  outro: {
    scale: 1,
    x: 0,
    y: 0,
    radius: 0,
    shadowOpacity: 0,
    dim: 0,
  },
};

export type ProductLaunchFilmProps = Readonly<{
  audio?: ProductAudioTrackProps["settings"];
  bgm?: ProductBgmTrackProps["settings"];
  launch?: Readonly<{
    enabled?: boolean;
    showProgress?: boolean;
    showChapterLabel?: boolean;
    accents?: LaunchAccentTrackSettings;
  }>;
}>;

type ActiveScene = Readonly<{
  key: ProductSceneKey;
  index: number;
  localFrame: number;
  duration: number;
}>;

const getActiveScene = (frame: number): ActiveScene => {
  const fallbackKey = SCENE_ORDER[SCENE_ORDER.length - 1];
  const key =
    SCENE_ORDER.find((candidate) => {
      const range = timeline[candidate];
      return frame >= range.from && frame < range.from + range.duration;
    }) ?? fallbackKey;
  const range = timeline[key];

  return {
    key,
    index: SCENE_ORDER.indexOf(key),
    localFrame: Math.max(0, frame - range.from),
    duration: range.duration,
  };
};

const mix = (from: number, to: number, progress: number): number => {
  return from + (to - from) * progress;
};

const blendConfig = (
  from: StageConfig,
  to: StageConfig,
  progress: number,
): StageConfig => ({
  scale: mix(from.scale, to.scale, progress),
  x: mix(from.x, to.x, progress),
  y: mix(from.y, to.y, progress),
  radius: mix(from.radius, to.radius, progress),
  shadowOpacity: mix(from.shadowOpacity, to.shadowOpacity, progress),
  dim: mix(from.dim, to.dim, progress),
});

const getStageConfig = (scene: ActiveScene): StageConfig => {
  const current = STAGE_CONFIGS[scene.key];
  const previousKey = SCENE_ORDER[Math.max(0, scene.index - 1)];
  const nextKey = SCENE_ORDER[Math.min(SCENE_ORDER.length - 1, scene.index + 1)];
  const previous = STAGE_CONFIGS[previousKey];
  const next = STAGE_CONFIGS[nextKey];
  const transitionFrames = Math.min(18, Math.floor(scene.duration / 4));

  if (scene.index > 0 && scene.localFrame < transitionFrames) {
    const progress = interpolate(
      scene.localFrame,
      [0, transitionFrames],
      [0, 1],
      {...CLAMP, easing: EASE_OUT},
    );

    return blendConfig(previous, current, progress);
  }

  if (
    scene.index < SCENE_ORDER.length - 1 &&
    scene.localFrame > scene.duration - transitionFrames
  ) {
    const progress = interpolate(
      scene.localFrame,
      [scene.duration - transitionFrames, scene.duration],
      [0, 1],
      {...CLAMP, easing: EASE_OUT},
    );

    return blendConfig(current, next, progress);
  }

  return current;
};

const getOverlayOpacity = (scene: ActiveScene): number => {
  const inFrames = Math.min(18, Math.floor(scene.duration / 4));
  const outFrames = Math.min(20, Math.floor(scene.duration / 4));

  return interpolate(
    scene.localFrame,
    [0, inFrames, scene.duration - outFrames, scene.duration],
    [0, 1, 1, 0],
    {...CLAMP, easing: EASE_OUT},
  );
};

const Eyebrow = ({children}: Readonly<{children: string}>) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 10,
      color: LAUNCH_FILM.colors.brand,
      fontSize: LAUNCH_FILM.typography.eyebrow,
      fontWeight: 800,
      letterSpacing: "0.12em",
      textTransform: "uppercase",
    }}
  >
    <span
      style={{
        width: 28,
        height: 4,
        borderRadius: 999,
        backgroundColor: LAUNCH_FILM.colors.lime,
      }}
    />
    {children}
  </div>
);

const FeatureChip = ({
  label,
  active = false,
}: Readonly<{label: string; active?: boolean}>) => (
  <div
    style={{
      display: "inline-flex",
      alignItems: "center",
      gap: 8,
      padding: "9px 13px",
      borderRadius: 999,
      border: `1px solid ${
        active ? "rgba(79, 157, 122, 0.28)" : LAUNCH_FILM.colors.border
      }`,
      backgroundColor: active
        ? LAUNCH_FILM.colors.limeSoft
        : "rgba(255, 255, 255, 0.82)",
      color: active
        ? "#236B4A"
        : LAUNCH_FILM.colors.textSecondary,
      fontSize: 15,
      fontWeight: 750,
      boxShadow: active ? "0 10px 28px rgba(79, 157, 122, 0.10)" : "none",
    }}
  >
    <span
      style={{
        width: 7,
        height: 7,
        borderRadius: 999,
        backgroundColor: active
          ? LAUNCH_FILM.colors.cta
          : "#C9CAD7",
      }}
    />
    {label}
  </div>
);

const SidePanel = ({
  side,
  children,
  opacity,
  localFrame,
}: Readonly<{
  side: "left" | "right";
  children: React.ReactNode;
  opacity: number;
  localFrame: number;
}>) => {
  const enter = interpolate(localFrame, [0, 20], [28, 0], {
    ...CLAMP,
    easing: EASE_OUT,
  });

  return (
    <div
      style={{
        position: "absolute",
        top: 0,
        bottom: 0,
        [side]: 0,
        width: 420,
        display: "flex",
        alignItems: "center",
        padding: side === "left" ? "0 0 0 58px" : "0 58px 0 0",
        boxSizing: "border-box",
        opacity,
        transform: `translateX(${side === "left" ? -enter : enter}px)`,
        pointerEvents: "none",
      }}
    >
      <div
        style={{
          width: "100%",
          padding: "34px 32px",
          borderRadius: LAUNCH_FILM.panel.radius,
          border: `1px solid ${LAUNCH_FILM.panel.border}`,
          background:
            "linear-gradient(180deg, rgba(255,255,255,0.94), rgba(248,249,253,0.90))",
          boxShadow: LAUNCH_FILM.panel.shadow,
          backdropFilter: "blur(18px)",
          WebkitBackdropFilter: "blur(18px)",
        }}
      >
        {children}
      </div>
    </div>
  );
};

const PanelTitle = ({children}: Readonly<{children: React.ReactNode}>) => (
  <div
    style={{
      marginTop: 18,
      color: LAUNCH_FILM.colors.text,
      fontSize: 48,
      fontWeight: 850,
      lineHeight: 1.08,
      letterSpacing: "-0.045em",
    }}
  >
    {children}
  </div>
);

const PanelBody = ({children}: Readonly<{children: React.ReactNode}>) => (
  <div
    style={{
      marginTop: 18,
      color: LAUNCH_FILM.colors.textSecondary,
      fontSize: 19,
      fontWeight: 520,
      lineHeight: 1.65,
    }}
  >
    {children}
  </div>
);

const LaunchOverlay = ({scene}: Readonly<{scene: ActiveScene}>) => {
  const opacity = getOverlayOpacity(scene);
  const localFrame = scene.localFrame;

  if (scene.key === "unsent") {
    return (
      <div
        style={{
          position: "absolute",
          left: 64,
          top: 52,
          opacity,
          pointerEvents: "none",
        }}
      >
        <Eyebrow>Social Lab · Product Film</Eyebrow>
      </div>
    );
  }

  if (scene.key === "landing") {
    return (
      <div
        style={{
          position: "absolute",
          right: 64,
          top: 54,
          display: "grid",
          justifyItems: "end",
          gap: 10,
          opacity,
          pointerEvents: "none",
        }}
      >
        <div
          style={{
            padding: "10px 14px",
            borderRadius: 999,
            backgroundColor: "rgba(255,255,255,0.86)",
            border: `1px solid ${LAUNCH_FILM.colors.border}`,
            color: LAUNCH_FILM.colors.brand,
            fontSize: 15,
            fontWeight: 800,
            boxShadow: LAUNCH_FILM.shadows.card,
          }}
        >
          AI 人际沟通预演
        </div>
        <div
          style={{
            color: LAUNCH_FILM.colors.textSecondary,
            fontSize: 16,
            fontWeight: 650,
          }}
        >
          先看见可能的回应，再决定怎么开口
        </div>
      </div>
    );
  }

  if (scene.key === "picker" || scene.key === "scenarioForm") {
    return (
      <SidePanel
        side="left"
        opacity={opacity}
        localFrame={localFrame}
      >
        <Eyebrow>01 · Context</Eyebrow>
        <PanelTitle>
          先理解场景，
          <br />
          再开始模拟。
        </PanelTitle>
        <PanelBody>
          目标、紧急程度、预期结果和潜在风险，共同决定一次沟通应该如何展开。
        </PanelBody>
        <div style={{display: "flex", flexWrap: "wrap", gap: 9, marginTop: 24}}>
          <FeatureChip label="沟通目标" active />
          <FeatureChip label="关系背景" />
          <FeatureChip label="风险约束" />
        </div>
      </SidePanel>
    );
  }

  if (scene.key === "personSetup") {
    return (
      <SidePanel
        side="right"
        opacity={opacity}
        localFrame={localFrame}
      >
        <Eyebrow>02 · Person</Eyebrow>
        <PanelTitle>
          模拟的不是“任何人”，
          <br />
          而是这个人。
        </PanelTitle>
        <PanelBody>
          将关系、沟通习惯和历史线索带入画像，让回应更接近真实对象，而不是通用聊天机器人。
        </PanelBody>
        <div style={{display: "grid", gap: 10, marginTop: 24}}>
          <FeatureChip label="身份与关系" active />
          <FeatureChip label="沟通习惯" active />
          <FeatureChip label="历史对话线索" active />
        </div>
      </SidePanel>
    );
  }

  if (scene.key === "persona") {
    return (
      <SidePanel
        side="left"
        opacity={opacity}
        localFrame={localFrame}
      >
        <Eyebrow>03 · Persona</Eyebrow>
        <PanelTitle>
          不是模板回复，
          <br />
          是有画像的模拟。
        </PanelTitle>
        <PanelBody>
          Persona 与 Relationship State 同时参与回应，让沟通风格、关注点和关系压力保持一致。
        </PanelBody>
        <div style={{display: "flex", flexWrap: "wrap", gap: 9, marginTop: 24}}>
          <FeatureChip label="沟通风格" active />
          <FeatureChip label="关系状态" active />
          <FeatureChip label="风险点" />
        </div>
      </SidePanel>
    );
  }

  if (scene.key === "conversation") {
    return (
      <SidePanel
        side="right"
        opacity={opacity}
        localFrame={localFrame}
      >
        <Eyebrow>04 · Rehearse</Eyebrow>
        <PanelTitle>
          在真正开口前，
          <br />
          先经历一次回应。
        </PanelTitle>
        <PanelBody>
          每一句话都会改变对方的态度、关注点和下一轮可能回应。练习的不只是措辞，也是节奏与判断。
        </PanelBody>
        <div style={{display: "grid", gap: 10, marginTop: 24}}>
          <FeatureChip label="画像一致的回应" active />
          <FeatureChip label="关系状态持续更新" active />
          <FeatureChip label="多轮对话演练" active />
        </div>
      </SidePanel>
    );
  }

  if (scene.key === "mechanism") {
    const titleProgress = spring({
      frame: localFrame,
      fps: VIDEO.fps,
      durationInFrames: 28,
      config: {damping: 190, stiffness: 150, mass: 0.8},
    });
    const titleY = interpolate(titleProgress, [0, 1], [22, 0], CLAMP);

    return (
      <div
        style={{
          position: "absolute",
          left: 0,
          right: 0,
          top: 40,
          display: "grid",
          justifyItems: "center",
          opacity,
          transform: `translateY(${titleY}px)`,
          pointerEvents: "none",
        }}
      >
        <Eyebrow>Under the hood</Eyebrow>
        <div
          style={{
            marginTop: 9,
            color: LAUNCH_FILM.colors.text,
            fontSize: 50,
            fontWeight: 850,
            letterSpacing: "-0.045em",
          }}
        >
          四个 Agent，协同完成一次判断
        </div>
      </div>
    );
  }

  if (scene.key === "dynamics") {
    return (
      <SidePanel
        side="left"
        opacity={opacity}
        localFrame={localFrame}
      >
        <Eyebrow>05 · Dynamics</Eyebrow>
        <PanelTitle>
          不只生成回答，
          <br />
          还持续更新判断。
        </PanelTitle>
        <PanelBody>
          从对话证据中更新关系状态、成功概率和关键影响，让每轮变化都有依据。
        </PanelBody>
        <div style={{display: "grid", gap: 10, marginTop: 24}}>
          <FeatureChip label="对话证据" active />
          <FeatureChip label="关系变化" active />
          <FeatureChip label="结果预测" active />
        </div>
      </SidePanel>
    );
  }

  if (scene.key === "report") {
    const scoreProgress = interpolate(
      localFrame,
      [12, Math.min(92, scene.duration - 24)],
      [0, 1],
      {...CLAMP, easing: EASE_OUT},
    );
    const score = Math.round(81 * scoreProgress);

    return (
      <SidePanel
        side="right"
        opacity={opacity}
        localFrame={localFrame}
      >
        <Eyebrow>06 · Report</Eyebrow>
        <div
          style={{
            marginTop: 18,
            display: "flex",
            alignItems: "baseline",
            gap: 8,
            color: LAUNCH_FILM.colors.brand,
          }}
        >
          <span
            style={{
              fontSize: LAUNCH_FILM.typography.metric,
              fontWeight: 850,
              letterSpacing: "-0.06em",
            }}
          >
            {score}
          </span>
          <span style={{fontSize: 18, fontWeight: 750}}>/ 100</span>
        </div>
        <PanelTitle>
          从结果，
          <br />
          到原因，再到下一步。
        </PanelTitle>
        <PanelBody>
          报告解释成功率为何变化、哪些表达影响最大，以及下一轮最值得尝试什么。
        </PanelBody>
      </SidePanel>
    );
  }

  if (scene.key === "rewrite") {
    const sweep = interpolate(
      localFrame,
      [16, Math.min(scene.duration - 22, 150)],
      [0, 1],
      {...CLAMP, easing: EASE_OUT},
    );
    const metricProgress = interpolate(
      localFrame,
      [Math.min(120, scene.duration * 0.55), Math.min(188, scene.duration - 12)],
      [0, 1],
      {...CLAMP, easing: EASE_OUT},
    );

    return (
      <SidePanel
        side="left"
        opacity={opacity}
        localFrame={localFrame}
      >
        <Eyebrow>07 · Rewrite → Retry</Eyebrow>
        <PanelTitle>
          推荐写作之后，
          <br />
          直接进入下一轮验证。
        </PanelTitle>
        <PanelBody>
          先解释原句问题，再重构表达结构，最后把推荐版本带回同一场景继续模拟。
        </PanelBody>

        <div style={{display: "grid", gap: 10, marginTop: 22}}>
          {[
            ["01", "识别问题", "依据、边界与请求范围"],
            ["02", "生成推荐表达", "保留事实，收束下一步"],
            ["03", "继续模拟", "同一画像下验证新回应"],
          ].map(([step, title, detail], index) => {
            const active = sweep >= (index + 1) / 3 - 0.12;
            return (
              <div
                key={step}
                style={{
                  display: "grid",
                  gridTemplateColumns: "38px 1fr",
                  gap: 12,
                  alignItems: "center",
                  padding: "12px 13px",
                  borderRadius: 15,
                  border: `1px solid ${
                    active ? "rgba(79,157,122,0.26)" : LAUNCH_FILM.colors.border
                  }`,
                  backgroundColor: active
                    ? LAUNCH_FILM.colors.limeSoft
                    : "rgba(255,255,255,0.72)",
                }}
              >
                <span
                  style={{
                    color: active
                      ? "#236B4A"
                      : LAUNCH_FILM.colors.textSecondary,
                    fontSize: 13,
                    fontWeight: 850,
                  }}
                >
                  {step}
                </span>
                <div>
                  <div
                    style={{
                      color: LAUNCH_FILM.colors.text,
                      fontSize: 15,
                      fontWeight: 820,
                    }}
                  >
                    {title}
                  </div>
                  <div
                    style={{
                      marginTop: 3,
                      color: LAUNCH_FILM.colors.textSecondary,
                      fontSize: 12,
                      fontWeight: 650,
                    }}
                  >
                    {detail}
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        <div
          style={{
            display: "grid",
            gridTemplateColumns: "repeat(3, minmax(0, 1fr))",
            gap: 8,
            marginTop: 18,
            opacity: metricProgress,
            transform: `translateY(${8 * (1 - metricProgress)}px)`,
          }}
        >
          {[
            ["+18", "清晰度"],
            ["+12", "回复意愿"],
            ["+21", "下一步"],
          ].map(([value, label]) => (
            <div
              key={label}
              style={{
                padding: "11px 8px",
                borderRadius: 14,
                backgroundColor: "rgba(255,255,255,0.84)",
                border: `1px solid ${LAUNCH_FILM.colors.border}`,
                textAlign: "center",
              }}
            >
              <div
                style={{
                  color: LAUNCH_FILM.colors.brand,
                  fontSize: 21,
                  fontWeight: 850,
                }}
              >
                {value}
              </div>
              <div
                style={{
                  marginTop: 3,
                  color: LAUNCH_FILM.colors.textSecondary,
                  fontSize: 11,
                  fontWeight: 750,
                }}
              >
                {label}
              </div>
            </div>
          ))}
        </div>
      </SidePanel>
    );
  }

  return null;
};

const ChapterLabel = ({scene}: Readonly<{scene: ActiveScene}>) => {
  if (scene.key === "unsent" || scene.key === "landing" || scene.key === "outro") {
    return null;
  }

  const chapterByScene: Partial<Record<ProductSceneKey, string>> = {
    picker: "建立沟通场景",
    scenarioForm: "明确目标与风险",
    personSetup: "还原真实对象",
    persona: "生成对象画像",
    conversation: "开始多轮演练",
    mechanism: "理解多智能体协作",
    dynamics: "观察状态变化",
    report: "解释沟通结果",
    rewrite: "改写并继续验证",
  };

  const label = chapterByScene[scene.key];
  if (!label) {
    return null;
  }

  return (
    <div
      style={{
        position: "absolute",
        left: 50,
        bottom: 34,
        display: "inline-flex",
        alignItems: "center",
        gap: 12,
        padding: "10px 14px",
        borderRadius: 999,
        border: `1px solid ${LAUNCH_FILM.colors.border}`,
        backgroundColor: "rgba(255,255,255,0.84)",
        color: LAUNCH_FILM.colors.textSecondary,
        boxShadow: LAUNCH_FILM.shadows.card,
        backdropFilter: "blur(14px)",
        WebkitBackdropFilter: "blur(14px)",
        fontSize: 14,
        fontWeight: 750,
        pointerEvents: "none",
      }}
    >
      <span style={{color: LAUNCH_FILM.colors.brand}}>
        {String(scene.index + 1).padStart(2, "0")}
      </span>
      <span style={{width: 1, height: 14, backgroundColor: LAUNCH_FILM.colors.border}} />
      {label}
    </div>
  );
};

const LAUNCH_MUTED_PRODUCT_CUES = [
  "scene-08-enter",
  "scene-08-panel-open",
  "scene-08-edge-draw",
  "scene-08-persona-agent",
  "scene-08-simulation-agent",
  "scene-08-state-agent",
  "scene-08-prediction-agent",
  "scene-08-mechanism-complete",
  "scene-11-enter",
  "scene-11-composer-fill",
  "scene-11-send-click",
  "scene-11-user-bubble",
  "scene-11-target-typing",
  "scene-11-target-response",
  "scene-11-score-update",
  "scene-11-willingness-up",
  "scene-11-warmth-up",
  "scene-11-clarity-up",
  "scene-11-loop-rewrite",
  "scene-11-loop-conversation",
  "scene-11-loop-compare",
  "scene-11-ad-settle",
] as const;

export const ProductLaunchFilm = ({
  audio,
  bgm,
  launch,
}: ProductLaunchFilmProps) => {
  const frame = useCurrentFrame();
  const {fps, width, height} = useVideoConfig();
  const scene = getActiveScene(frame);
  const stage = getStageConfig(scene);
  const launchEnabled = launch?.enabled ?? true;
  const showProgress = launch?.showProgress ?? true;
  const showChapterLabel = launch?.showChapterLabel ?? true;
  const filmProgress = interpolate(
    frame,
    [0, PRODUCT_FILM_DURATION - 1],
    [0, 1],
    CLAMP,
  );
  const ambientX = interpolate(
    frame,
    [0, PRODUCT_FILM_DURATION - 1],
    [-80, 120],
    CLAMP,
  );
  const ambientY = interpolate(
    frame,
    [0, PRODUCT_FILM_DURATION - 1],
    [80, -40],
    CLAMP,
  );
  const openingGlow = spring({
    frame,
    fps,
    durationInFrames: 54,
    config: {damping: 200, stiffness: 90, mass: 0.9},
  });
  const renderScale = Math.min(width / VIDEO.width, height / VIDEO.height);
  const launchMutedCueIds = Array.from(
    new Set([
      ...(audio?.mutedCueIds ?? []),
      ...LAUNCH_MUTED_PRODUCT_CUES,
    ]),
  );
  const launchAudio = {
    ...audio,
    mutedCueIds: launchMutedCueIds,
  };

  if (!launchEnabled) {
    return (
      <AbsoluteFill style={{overflow: "hidden", backgroundColor: LAUNCH_FILM.colors.surface}}>
        <div
          style={{
            position: "absolute",
            left: "50%",
            top: "50%",
            width: VIDEO.width,
            height: VIDEO.height,
            transform: `translate(-50%, -50%) scale(${renderScale})`,
            transformOrigin: "center center",
          }}
        >
          <ProductDemo
            audio={{...audio, enabled: false}}
            bgm={{...bgm, enabled: false}}
          />
        </div>
        <ProductBgmTrack settings={bgm} />
        <ProductAudioTrack settings={audio} />
      </AbsoluteFill>
    );
  }

  return (
    <AbsoluteFill
      style={{
        overflow: "hidden",
        background:
          `linear-gradient(180deg, ${LAUNCH_FILM.background.soft} 0%, ` +
          `${LAUNCH_FILM.background.base} 100%)`,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: "50%",
          top: "50%",
          width: VIDEO.width,
          height: VIDEO.height,
          transform: `translate(-50%, -50%) scale(${renderScale})`,
          transformOrigin: "center center",
        }}
      >
        <AbsoluteFill
          style={{
            overflow: "hidden",
            background:
              `linear-gradient(180deg, ${LAUNCH_FILM.background.soft} 0%, ` +
              `${LAUNCH_FILM.background.base} 100%)`,
            color: LAUNCH_FILM.colors.text,
            fontFamily: LAUNCH_FILM.typography.family,
          }}
        >
          <div
            style={{
              position: "absolute",
              inset: 0,
              opacity: 0.7,
              backgroundImage:
                `linear-gradient(${LAUNCH_FILM.background.grid} 1px, transparent 1px), ` +
                `linear-gradient(90deg, ${LAUNCH_FILM.background.grid} 1px, transparent 1px)`,
              backgroundSize: "64px 64px",
              maskImage:
                "linear-gradient(180deg, rgba(0,0,0,0.85), rgba(0,0,0,0.15))",
            }}
          />
          <div
            style={{
              position: "absolute",
              left: -220 + ambientX,
              top: -260 + ambientY,
              width: 760,
              height: 760,
              borderRadius: 999,
              background: `radial-gradient(circle, ${LAUNCH_FILM.background.glowLavender} 0%, transparent 68%)`,
              opacity: 0.72 * openingGlow,
              filter: "blur(10px)",
            }}
          />
          <div
            style={{
              position: "absolute",
              right: -300 - ambientX * 0.5,
              bottom: -350 - ambientY * 0.4,
              width: 880,
              height: 880,
              borderRadius: 999,
              background: `radial-gradient(circle, ${LAUNCH_FILM.background.glowLime} 0%, transparent 70%)`,
              opacity: 0.58,
              filter: "blur(14px)",
            }}
          />

          <div
            style={{
              position: "absolute",
              left: "50%",
              top: "50%",
              width: VIDEO.width,
              height: VIDEO.height,
              overflow: "hidden",
              borderRadius: stage.radius,
              border:
                stage.radius > 0
                  ? `1px solid ${LAUNCH_FILM.window.border}`
                  : "1px solid transparent",
              backgroundColor: LAUNCH_FILM.colors.surface,
              boxShadow:
                stage.shadowOpacity > 0
                  ? `0 42px 120px rgba(35, 36, 58, ${0.2 * stage.shadowOpacity})`
                  : "none",
              transform:
                `translate(-50%, -50%) translate(${stage.x}px, ${stage.y}px) ` +
                `scale(${stage.scale})`,
              transformOrigin: "center center",
              willChange: "transform, border-radius, box-shadow",
            }}
          >
            <ProductDemo
              audio={{...audio, enabled: false}}
              bgm={{...bgm, enabled: false}}
            />
            {stage.dim > 0 ? (
              <AbsoluteFill
                style={{
                  backgroundColor: `rgba(23, 24, 43, ${stage.dim})`,
                  pointerEvents: "none",
                }}
              />
            ) : null}
          </div>

          <LaunchOverlay scene={scene} />
          {showChapterLabel ? <ChapterLabel scene={scene} /> : null}

          {showProgress ? (
            <div
              style={{
                position: "absolute",
                left: 0,
                right: 0,
                top: 0,
                height: 6,
                backgroundColor: "rgba(47,47,99,0.08)",
              }}
            >
              <div
                style={{
                  width: `${filmProgress * 100}%`,
                  height: "100%",
                  borderRadius: "0 999px 999px 0",
                  background:
                    "linear-gradient(90deg, #2F2F63 0%, #4F9D7A 62%, #C8F47A 100%)",
                }}
              />
            </div>
          ) : null}
        </AbsoluteFill>
      </div>

      <ProductBgmTrack settings={bgm} />
      <ProductAudioTrack settings={launchAudio} />
      <LaunchAccentTrack settings={launch?.accents} />
    </AbsoluteFill>
  );
};
