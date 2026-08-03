import {useLayoutEffect} from "react";
import type {CSSProperties, ReactNode} from "react";
import {
  Easing,
  interpolate,
  useCurrentFrame,
} from "remotion";

import {
  ProductAudioTrack,
  type ProductAudioTrackProps,
} from "../audio/ProductAudioTrack";
import {
  ProductBgmTrack,
  type ProductBgmTrackProps,
} from "../audio/ProductBgmTrack";
import {PRODUCT_MOBILE_THEME as THEME} from "../design/mobile-product-theme";
import {timeline} from "../timeline/product-film";

export const MOBILE_VIDEO = {
  width: THEME.viewport.outputWidth,
  height: THEME.viewport.outputHeight,
} as const;

const C = THEME.colors;
const L = THEME.layout;
const R = THEME.radii;
const S = THEME.shadows;
const SCALE = THEME.viewport.outputWidth / THEME.viewport.width;
const FONT = 'Inter, "PingFang SC", "Microsoft YaHei", Arial, sans-serif';
const CLAMP = {extrapolateLeft: "clamp", extrapolateRight: "clamp"} as const;
const EASE = Easing.bezier(0.16, 1, 0.3, 1);

const opacityIn = (frame: number, from: number, duration = 10) =>
  interpolate(frame, [from, from + duration], [0, 1], {...CLAMP, easing: EASE});
const riseIn = (frame: number, from: number, distance = 16, duration = 14) =>
  interpolate(frame, [from, from + duration], [distance, 0], {...CLAMP, easing: EASE});
const reveal = (frame: number, from: number, distance = 16): CSSProperties => ({
  opacity: opacityIn(frame, from),
  transform: `translateY(${riseIn(frame, from, distance)}px)`,
});
const pressScale = (frame: number, at: number) =>
  interpolate(frame, [at - 3, at, at + 5, at + 9], [1, 0.975, 0.985, 1], CLAMP);
const typeText = (frame: number, from: number, to: number, value: string) => {
  const count = Math.floor(interpolate(frame, [from, to], [0, value.length], CLAMP));
  return value.slice(0, count);
};

type IconGlyphProps = Readonly<{
  name: string;
  strokeWidth: number;
}>;

const IconGlyph = ({name, strokeWidth}: IconGlyphProps) => {
  const common = {
    fill: "none",
    stroke: "currentColor",
    strokeWidth,
    strokeLinecap: "round" as const,
    strokeLinejoin: "round" as const,
  };

  switch (name) {
    case "back":
      return <><path {...common} d="M19 12H5"/><path {...common} d="m12 19-7-7 7-7"/></>;
    case "brain":
      return <><path {...common} d="M9.5 4.5A3 3 0 0 0 6 7.4 3.5 3.5 0 0 0 5 14a3 3 0 0 0 3 3h1.5"/><path {...common} d="M14.5 4.5A3 3 0 0 1 18 7.4a3.5 3.5 0 0 1 1 6.6 3 3 0 0 1-3 3h-1.5"/><path {...common} d="M12 3v18M8 9h4m0 6h4"/></>;
    case "sparkle":
      return <><path {...common} d="m12 3 1.2 4.2L17 9l-3.8 1.8L12 15l-1.2-4.2L7 9l3.8-1.8L12 3Z"/><path {...common} d="m19 15 .6 2.1L22 18l-2.4.9L19 21l-.6-2.1L16 18l2.4-.9L19 15Z"/></>;
    case "arrow":
      return <><path {...common} d="M5 12h14"/><path {...common} d="m13 6 6 6-6 6"/></>;
    case "home":
      return <><path {...common} d="m3 11 9-8 9 8"/><path {...common} d="M5 10v10h14V10M9 20v-6h6v6"/></>;
    case "persona":
      return <><circle {...common} cx="12" cy="8" r="4"/><path {...common} d="M4 21a8 8 0 0 1 16 0"/></>;
    case "chat":
      return <path {...common} d="M21 15a4 4 0 0 1-4 4H8l-5 3 1.6-4A7 7 0 0 1 3 13V8a4 4 0 0 1 4-4h10a4 4 0 0 1 4 4v7Z"/>;
    case "report":
      return <><path {...common} d="M6 3h12v18H6z"/><path {...common} d="M9 8h6M9 12h6M9 16h4"/></>;
    case "send":
      return <><path {...common} d="m22 2-7 20-4-9-9-4 20-7Z"/><path {...common} d="M22 2 11 13"/></>;
    case "refresh":
      return <><path {...common} d="M20 7h-5V2"/><path {...common} d="M20 7a8 8 0 1 0 1 8"/></>;
    case "check":
      return <path {...common} d="m5 12 4 4L19 6"/>;
    case "copy":
      return <><rect {...common} x="8" y="8" width="11" height="12" rx="2"/><path {...common} d="M16 8V6a2 2 0 0 0-2-2H6a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h2"/></>;
    case "close":
      return <><path {...common} d="m6 6 12 12M18 6 6 18"/></>;
    case "chevron":
      return <path {...common} d="m6 9 6 6 6-6"/>;
    case "sliders":
      return <><path {...common} d="M4 7h10M18 7h2M4 17h2M10 17h10"/><circle {...common} cx="16" cy="7" r="2"/><circle {...common} cx="8" cy="17" r="2"/></>;
    case "cap":
      return <><path {...common} d="m2 10 10-5 10 5-10 5-10-5Z"/><path {...common} d="M6 12v5c3 2 9 2 12 0v-5"/></>;
    case "briefcase":
      return <><rect {...common} x="3" y="7" width="18" height="13" rx="2"/><path {...common} d="M8 7V5h8v2M3 12h18M10 12v2h4v-2"/></>;
    case "heart":
      return <path {...common} d="M20.8 4.6a5.5 5.5 0 0 0-7.8 0L12 5.7l-1.1-1.1a5.5 5.5 0 0 0-7.8 7.8l1.1 1.1L12 21l7.8-7.5 1.1-1.1a5.5 5.5 0 0 0-.1-7.8Z"/>;
    default:
      return <><path {...common} d="m12 3 1.2 4.2L17 9l-3.8 1.8L12 15l-1.2-4.2L7 9l3.8-1.8L12 3Z"/><path {...common} d="m19 15 .6 2.1L22 18l-2.4.9L19 21l-.6-2.1L16 18l2.4-.9L19 15Z"/></>;
  }
};

const Icon = ({name, size = 20, strokeWidth = 2}: Readonly<{name: string; size?: number; strokeWidth?: number}>) => (
  <svg
    viewBox="0 0 24 24"
    width={size}
    height={size}
    aria-hidden="true"
    focusable="false"
    style={{display: "block"}}
  >
    <IconGlyph name={name} strokeWidth={strokeWidth}/>
  </svg>
);

const ProductViewport = ({children}: Readonly<{children: ReactNode}>) => (
  <div
    className="notranslate"
    lang="zh-CN"
    translate="no"
    style={{
      position: "absolute",
      inset: 0,
      overflow: "hidden",
      background: C.page,
    }}
  >
    <div
      style={{
        position: "absolute",
        left: 0,
        top: 0,
        width: THEME.viewport.width,
        height: THEME.viewport.height,
        overflow: "hidden",
        transform: `scale(${SCALE})`,
        transformOrigin: "top left",
        fontFamily: FONT,
        color: C.ink,
        background: C.page,
      }}
    >
      {children}
    </div>
  </div>
);

const STEP_LABELS = ["先演练，再开口", "沟通目标", "对方信息", "对象画像", "模拟对话", "沟通报告"] as const;
const NAV = [
  {icon: "home", label: "准备", step: 0},
  {icon: "persona", label: "画像", step: 3},
  {icon: "chat", label: "对话", step: 4},
  {icon: "report", label: "报告", step: 5},
] as const;

const ProductShell = ({
  step,
  children,
  contentStyle,
  hideNav = false,
  overlay,
  subtitleOverride,
}: Readonly<{
  step: number;
  children: ReactNode;
  contentStyle?: CSSProperties;
  hideNav?: boolean;
  overlay?: ReactNode;
  subtitleOverride?: string;
}>) => {
  const progress = step <= 0 ? 0 : (step / 5) * 100;
  const activeNav = step <= 2 ? 0 : step === 3 ? 1 : step === 4 ? 2 : 3;
  return (
    <ProductViewport>
      <div style={{position: "absolute", inset: 0, background: C.page}}>
        <header
          style={{
            position: "absolute",
            left: L.sidePadding,
            right: L.sidePadding,
            top: 0,
            height: L.headerHeight,
            display: "grid",
            gridTemplateColumns: "44px 1fr 44px",
            alignItems: "center",
            background: "rgba(244,246,251,0.94)",
            borderBottom: `1px solid ${C.borderSoft}`,
            zIndex: 30,
          }}
        >
          <div style={{width: 44, height: 44, borderRadius: R.icon, display: "grid", placeItems: "center", color: C.primary, background: C.surface, boxShadow: S.soft}}>
            <Icon name="back" size={20}/>
          </div>
          <div style={{textAlign: "center"}}>
            <strong style={{display: "block", fontSize: 21, lineHeight: 1.16}}>Social Lab</strong>
            <span style={{display: "block", color: C.muted, fontSize: 12, marginTop: 2}}>
              {subtitleOverride ?? (step === 0 ? STEP_LABELS[0] : `Step ${step} / 5 · ${STEP_LABELS[step]}`)}
            </span>
          </div>
          <div style={{width: 44, height: 44, borderRadius: R.icon, display: "grid", placeItems: "center", color: C.primary, background: C.surface, boxShadow: S.soft}}>
            <Icon name="brain" size={20}/>
          </div>
        </header>
        {step > 0 && (
          <div style={{position: "absolute", left: L.sidePadding, right: L.sidePadding, top: L.headerHeight, height: L.progressHeight, borderRadius: 999, overflow: "hidden", background: "#E2DED6", zIndex: 31}}>
            <div style={{width: `${progress}%`, height: "100%", background: "#9CAD9A", borderRadius: 999}}/>
          </div>
        )}
        <main
          style={{
            position: "absolute",
            left: L.sidePadding,
            right: L.sidePadding,
            top: L.headerHeight + (step > 0 ? L.progressHeight + 18 : 16),
            bottom: hideNav ? 0 : L.bottomNavHeight,
            overflow: "hidden",
            ...contentStyle,
          }}
        >
          {children}
        </main>
        {!hideNav && (
          <nav style={{position: "absolute", left: 0, right: 0, bottom: 0, height: L.bottomNavHeight, display: "grid", gridTemplateColumns: "repeat(4, 1fr)", gap: 8, padding: "10px 14px 12px", background: "rgba(255,255,255,0.96)", borderTop: "1px solid #DCE1E7", boxShadow: S.nav, zIndex: 50}}>
            {NAV.map((item, index) => (
              <div key={item.label} style={{minHeight: 58, borderRadius: 18, display: "grid", placeItems: "center", alignContent: "center", gap: 3, background: index === activeNav ? C.nav : "transparent", color: index === activeNav ? C.navInk : C.navMuted, fontSize: 12, fontWeight: 800, opacity: item.step > step ? 0.48 : 1}}>
                <Icon name={item.icon} size={19}/><span>{item.label}</span>
              </div>
            ))}
          </nav>
        )}
        {overlay}
      </div>
    </ProductViewport>
  );
};

const Card = ({children, style}: Readonly<{children: ReactNode; style?: CSSProperties}>) => (
  <div style={{background: C.surface, border: `1px solid ${C.line}`, borderRadius: R.card, boxShadow: S.soft, padding: 22, ...style}}>{children}</div>
);
const Button = ({children, style, disabled = false}: Readonly<{children: ReactNode; style?: CSSProperties; disabled?: boolean}>) => (
  <div style={{minHeight: 58, borderRadius: 20, display: "flex", alignItems: "center", justifyContent: "center", gap: 8, padding: "0 22px", background: disabled ? "#C7CDD2" : C.action, color: "#FFF", fontSize: 19, fontWeight: 800, boxShadow: disabled ? "none" : S.action, ...style}}>{children}</div>
);
const SecondaryButton = ({children, style}: Readonly<{children: ReactNode; style?: CSSProperties}>) => (
  <div style={{minHeight: 46, borderRadius: R.button, display: "flex", alignItems: "center", justifyContent: "center", gap: 7, padding: "0 16px", background: C.surface, color: C.primary, border: `1px solid ${C.line}`, fontSize: 15, fontWeight: 800, ...style}}>{children}</div>
);
const Chip = ({children, selected = false}: Readonly<{children: ReactNode; selected?: boolean}>) => (
  <div style={{minHeight: 42, display: "inline-flex", alignItems: "center", padding: "0 16px", border: `1px solid ${selected ? C.selectedBorder : "#DDD8CE"}`, borderRadius: 999, background: selected ? C.selected : "#FFFDFA", color: selected ? C.selectedInk : C.navInk, fontWeight: 800, fontSize: 14, boxShadow: selected ? `inset 0 0 0 1px ${C.selectedBorder}` : undefined}}>{children}</div>
);
const Field = ({label, value, placeholder, focused = false, multiline = false}: Readonly<{label: string; value?: string; placeholder: string; focused?: boolean; multiline?: boolean}>) => (
  <label style={{display: "block"}}>
    <span style={{display: "block", marginBottom: 9, fontSize: 17, fontWeight: 800}}>{label}</span>
    <div style={{minHeight: multiline ? 98 : 48, borderRadius: R.input, border: `1px solid ${focused ? C.primary : C.line}`, background: C.surface, padding: multiline ? "14px 16px" : "13px 16px", fontSize: 14, lineHeight: 1.6, color: value ? C.ink : C.faint, boxShadow: focused ? "0 0 0 4px rgba(47,47,99,0.10)" : undefined, whiteSpace: "pre-wrap"}}>{value || placeholder}</div>
  </label>
);
const Tap = ({frame, at, x, y, color = C.primary}: Readonly<{frame: number; at: number; x: number; y: number; color?: string}>) => {
  const visible = frame >= at - 2 && frame <= at + 12;
  const p = interpolate(frame, [at - 2, at + 10], [0, 1], CLAMP);
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        left: x,
        top: y,
        width: 34 + p * 26,
        height: 34 + p * 26,
        marginLeft: -(17 + p * 13),
        marginTop: -(17 + p * 13),
        borderRadius: 999,
        border: `2px solid ${color}`,
        opacity: visible ? 1 - p : 0,
        visibility: visible ? "visible" : "hidden",
        zIndex: 80,
      }}
    />
  );
};
const Spinner = ({frame, size = 18}: Readonly<{frame: number; size?: number}>) => (
  <div style={{width: size, height: size, borderRadius: 999, border: "2px solid rgba(255,255,255,0.42)", borderTopColor: "#FFF", transform: `rotate(${frame * 14}deg)`}}/>
);
const smoothScroll = (
  frame: number,
  start: number,
  end: number,
  from: number,
  to: number,
) => interpolate(frame, [start, end], [from, to], {...CLAMP, easing: EASE});

const AnchoredTap = ({
  frame,
  at,
  color = C.primary,
}: Readonly<{frame: number; at: number; color?: string}>) => {
  const visible = frame >= at - 2 && frame <= at + 12;
  const p = interpolate(frame, [at - 2, at + 10], [0, 1], CLAMP);
  return (
    <div
      aria-hidden="true"
      style={{
        position: "absolute",
        left: "50%",
        top: "50%",
        width: 34 + p * 26,
        height: 34 + p * 26,
        transform: "translate(-50%, -50%)",
        borderRadius: 999,
        border: `2px solid ${color}`,
        opacity: visible ? 1 - p : 0,
        visibility: visible ? "visible" : "hidden",
        pointerEvents: "none",
        zIndex: 80,
      }}
    />
  );
};

const LandingContent = ({
  revealFrame,
  interactionFrame = 0,
  clickable = false,
}: Readonly<{
  revealFrame: number;
  interactionFrame?: number;
  clickable?: boolean;
}>) => {
  const buttonAt = 30;
  const scenarios = [
    {icon: "cap", label: "导师", summary: "推荐信 / 催回复", bg: C.advisor, iconBg: C.advisorIcon},
    {icon: "briefcase", label: "职场", summary: "加薪 / 汇报", bg: C.work, iconBg: C.workIcon},
    {icon: "heart", label: "社交", summary: "道歉 / 拒绝", bg: C.social, iconBg: C.socialIcon},
  ];
  return <>
    <div style={{minHeight: 360, padding: "24px 28px", borderRadius: 32, background: C.surface, border: `1px solid ${C.borderSoft}`, boxShadow: S.card, display: "flex", flexDirection: "column", justifyContent: "center", ...reveal(revealFrame, 0)}}>
      <div style={{width: "fit-content", padding: "8px 11px", borderRadius: 16, display: "inline-flex", alignItems: "center", gap: 7, background: C.lavender, color: C.primary, fontSize: 13, fontWeight: 800}}><Icon name="sparkle" size={15}/> AI 人际沟通预演</div>
      <h1 style={{margin: "18px 0 14px", fontSize: 42, lineHeight: 1.06, fontWeight: 800, letterSpacing: 0}}>先演练，<br/>再开口。</h1>
      <p style={{margin: 0, color: C.muted, fontSize: 16, lineHeight: 1.68}}>在真实沟通前，先和 AI 生成的关系数字分身练习一遍，预判风险，并获得更稳妥的表达方式。</p>
      <div style={{position: "relative", marginTop: 22, transform: `scale(${clickable ? pressScale(interactionFrame, buttonAt) : 1})`}}>
        <Button>开始模拟 <Icon name="arrow" size={18}/></Button>
        {clickable && <AnchoredTap frame={interactionFrame} at={buttonAt}/>} 
      </div>
    </div>
    <div style={{marginTop: 30, marginBottom: 12, ...reveal(revealFrame, 18)}}>
      <h2 style={{fontSize: 20, margin: 0}}>常见场景</h2>
      <p style={{fontSize: 14, color: C.muted, margin: "4px 0 0"}}>选择后会自动带入后续表单。</p>
    </div>
    <div style={{display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10}}>
      {scenarios.map((s, i) => <div key={s.label} style={{minHeight: 132, padding: 12, borderRadius: 22, border: `1px solid ${C.line}`, background: s.bg, ...reveal(revealFrame, 24 + i * 5, 10)}}>
        <div style={{width: 42, height: 42, borderRadius: 14, display: "grid", placeItems: "center", background: s.iconBg, color: "#FFF"}}><Icon name={s.icon} size={20}/></div>
        <b style={{display: "block", fontSize: 17, marginTop: 12}}>{s.label}</b>
        <span style={{display: "block", color: "#5C6B80", fontSize: 12, lineHeight: 1.35, marginTop: 2}}>{s.summary}</span>
      </div>)}
    </div>
  </>;
};

type MobileSceneProps = Readonly<{frame: number}>;

const MobileIntroScene = ({frame}: MobileSceneProps) => {
  return <ProductShell step={0}><LandingContent revealFrame={frame}/></ProductShell>;
};

const MobileLandingScene = ({frame}: MobileSceneProps) => {
  return <ProductShell step={0}><LandingContent revealFrame={timeline.unsent.duration} interactionFrame={frame} clickable/></ProductShell>;
};

const MobilePickerScene = ({frame}: MobileSceneProps) => {
  const open = opacityIn(frame, 4, 10);
  const selectAt = 72;
  const selected = frame >= selectAt;
  const exitProgress = interpolate(frame, [88, 144], [0, 1], {...CLAMP, easing: EASE});
  const modalScale = interpolate(frame, [4, 18], [0.94, 1], {...CLAMP, easing: EASE}) * (1 - exitProgress * 0.035);
  const options = [
    {icon: "cap", title: "导师沟通", copy: "申请推荐信、催回复或讨论项目", bg: C.advisor, iconBg: C.advisorIcon},
    {icon: "briefcase", title: "职场沟通", copy: "汇报、边界、加薪或绩效反馈", bg: C.work, iconBg: C.workIcon},
    {icon: "heart", title: "社交沟通", copy: "道歉、拒绝、解释误会或修复关系", bg: C.social, iconBg: C.socialIcon},
  ];
  const overlay = (
    <div style={{position: "absolute", inset: 0, zIndex: 60, display: "grid", placeItems: "center", padding: 24, opacity: open * (1 - exitProgress), transform: `translateY(${-exitProgress * 12}px)`}}>
      <div style={{position: "absolute", inset: 0, background: "rgba(20,22,34,0.58)"}}/>
      <div style={{position: "relative", width: "100%", padding: "44px 20px 20px", borderRadius: 30, background: "#15182B", color: "#FFF", boxShadow: "0 24px 70px rgba(14,16,26,0.38)", transform: `scale(${modalScale})`}}>
        <div style={{position: "absolute", left: "50%", top: -25, transform: "translateX(-50%) rotate(-5deg)", width: "max-content", padding: "10px 20px", borderRadius: 999, background: "#FFF05B", color: "#081122", fontSize: 20, fontWeight: 900}}>选择你的沟通场景</div>
        <div style={{display: "grid", gap: 10}}>
          {options.map((o, i) => <div key={o.title} style={{minHeight: 112, padding: 14, borderRadius: 18, display: "grid", gridTemplateColumns: "48px 1fr 22px", gap: 13, alignItems: "center", background: selected && i === 0 ? C.selected : o.bg, color: "#081122", border: selected && i === 0 ? `2px solid ${C.selectedBorder}` : "2px solid transparent", ...reveal(frame, 16 + i * 6, 12)}}>
            <div style={{width: 44, height: 44, borderRadius: 14, display: "grid", placeItems: "center", background: o.iconBg, color: "#FFF"}}><Icon name={o.icon} size={20}/></div>
            <div><b style={{fontSize: 18}}>{o.title}</b><span style={{display: "block", marginTop: 5, color: "#60738B", fontSize: 13, lineHeight: 1.4}}>{o.copy}</span></div>
            <div style={{width: 20, height: 20, borderRadius: 999, border: `2px solid ${selected && i === 0 ? C.selectedBorder : "#9BA4B3"}`, display: "grid", placeItems: "center", color: C.selectedInk}}><span style={{opacity:selected && i === 0 ? 1 : 0}}><Icon name="check" size={13}/></span></div>
          </div>)}
        </div>
        <p style={{margin: "16px 0 0", textAlign: "center", color: "rgba(255,255,255,0.62)", fontSize: 13}}>选择后仍可在下一步修改沟通目标。</p>
      </div>
      <Tap frame={frame} at={selectAt} x={215} y={278} color={C.selectedInk}/>
    </div>
  );
  return <ProductShell step={0} overlay={overlay}><LandingContent revealFrame={999}/></ProductShell>;
};

const QuestionCard = ({number, title, hint, children, complete = false, style}: Readonly<{number: number; title: string; hint: string; children: ReactNode; complete?: boolean; style?: CSSProperties}>) => (
  <div style={{padding: 20, border: "1px solid #DED9CE", borderRadius: 28, background: "rgba(255,255,253,0.9)", boxShadow: S.soft, ...style}}>
    <div style={{display: "grid", gridTemplateColumns: "36px 1fr", gap: 14, alignItems: "start", marginBottom: 18}}>
      <div style={{width: 36, height: 36, borderRadius: 999, display: "grid", placeItems: "center", background: complete ? C.selectedBorder : "#E4EBF1", color: complete ? "#FFF" : "#6F86A2", fontWeight: 800}}>{complete ? <Icon name="check" size={17}/> : number}</div>
      <div><h3 style={{margin: "2px 0 4px", fontSize: 20}}>{title}</h3><p style={{margin: 0, color: C.muted, fontSize: 14, lineHeight: 1.4}}>{hint}</p></div>
    </div>
    {children}
  </div>
);

const MobileScenarioFormScene = ({frame}: MobileSceneProps) => {
  const scroll =
    smoothScroll(frame, 52, 84, 0, -180) +
    smoothScroll(frame, 116, 148, 0, -225) +
    smoothScroll(frame, 176, 208, 0, -190);
  const chosenTask = frame >= 34;
  const chosenUrgency = frame >= 96;
  const outcome = typeText(frame, 124, 168, "希望导师确认下一步，并指出最需要优先验证的方向。");
  const concern = frame >= 190;
  return <ProductShell step={1} contentStyle={{overflow: "hidden"}}>
    <div style={{position: "relative", transform: `translateY(${scroll}px)`, willChange: "transform"}}>
      <div style={reveal(frame, 0)}><h2 style={{fontSize: 34, lineHeight: 1.12, margin: "0 0 10px"}}>这次你想解决什么沟通问题？</h2><p style={{fontSize: 17, lineHeight: 1.7, color: C.muted, margin: "0 0 26px"}}>先描述这次沟通任务，下一步再补充对方是谁。</p></div>
      <div style={{display: "grid", gap: 18}}>
        <QuestionCard number={1} title="这次你想沟通什么？" hint="单选 + 自定义 · 可跳过" complete={chosenTask}>
          <div style={{display: "flex", flexWrap: "wrap", gap: "10px 12px", marginBottom: 16}}>{["申请推荐信","催回复","申请延期","预约沟通"].map((x) => <div key={x} style={{position: "relative", display: "inline-flex"}}><Chip selected={chosenTask && x === "催回复"}>{x}</Chip>{x === "催回复" && <AnchoredTap frame={frame} at={32}/>}</div>)}</div>
          <div style={{padding: "14px 16px", borderRadius: R.input, background: "#FBFAF7", color: chosenTask ? C.ink : C.faint, fontSize: 14}}>{chosenTask ? "想请导师确认项目的下一步方向" : "例如：我想请导师帮我写推荐信"}</div>
        </QuestionCard>
        <QuestionCard number={2} title="这件事有多紧急？" hint="单选 · 可跳过" complete={chosenUrgency}>
          <div style={{display: "flex", flexWrap: "wrap", gap: "10px 12px"}}>{["不着急，只是提前沟通","一周内需要回复","三天内需要回复"].map((x) => <div key={x} style={{position: "relative", display: "inline-flex"}}><Chip selected={chosenUrgency && x === "一周内需要回复"}>{x}</Chip>{x === "一周内需要回复" && <AnchoredTap frame={frame} at={94}/>}</div>)}</div>
        </QuestionCard>
        <QuestionCard number={3} title="你希望这次沟通达到什么结果？" hint="文本输入，可选 · 可跳过" complete={outcome.length > 8}>
          <div style={{minHeight: 92, padding: "14px 16px", borderRadius: R.input, background: "#FBFAF7", color: outcome ? C.ink : C.faint, fontSize: 14, lineHeight: 1.6}}>{outcome || "例如：希望导师愿意帮我写推荐信，并且不要觉得我太唐突。"}</div>
        </QuestionCard>
        <QuestionCard number={4} title="你最担心哪里出问题？" hint="多选 + 可自定义 · 可跳过" complete={concern}>
          <div style={{display: "flex", flexWrap: "wrap", gap: "10px 12px"}}>{["担心显得不够配合","担心请求被拒绝","担心影响之后评价"].map((x) => <Chip key={x}>{x}</Chip>)}<div style={{position: "relative", display: "inline-flex"}}><Chip selected={concern}>担心对方不认真听</Chip><AnchoredTap frame={frame} at={188}/></div></div>
        </QuestionCard>
        <div style={{position: "relative", paddingBottom: 24, transform: `scale(${pressScale(frame, 218)})`}}><Button>继续补充对方信息 <Icon name="arrow" size={18}/></Button><AnchoredTap frame={frame} at={218}/></div>
      </div>
    </div>
  </ProductShell>;
};

const MobilePersonSetupScene = ({frame}: MobileSceneProps) => {
  const scroll =
    smoothScroll(frame, 32, 56, 0, -92) +
    smoothScroll(frame, 72, 102, 0, -146) +
    smoothScroll(frame, 112, 140, 0, -150) +
    smoothScroll(frame, 142, 168, 0, -112);
  const role = typeText(frame, 10, 36, "研究导师");
  const relation = typeText(frame, 42, 68, "合作顺畅，但平时联系不多");
  const habit = typeText(frame, 74, 108, "回复慢，比较严谨，喜欢有逻辑和证据");
  const chat = typeText(frame, 112, 140, "我：老师，想确认下一步。\n导师：请先整理阶段结果。");
  const loading = frame >= 160;
  return <ProductShell step={2} contentStyle={{overflow: "hidden"}}>
    <div style={{position: "relative", transform: `translateY(${scroll}px)`, willChange: "transform"}}>
      <div style={reveal(frame, 0)}><h2 style={{fontSize: 30, margin: "0 0 8px"}}>你希望 AI 扮演谁？</h2><p style={{fontSize: 17, lineHeight: 1.7, color: C.muted, margin: "0 0 18px"}}>请补充对方的信息。你将在后续对话中扮演自己，AI 会扮演这个沟通对象。</p></div>
      <div style={{display: "grid", gap: 14}}>
        <Field label="你想让 AI 扮演谁？" value={role} placeholder="例如：导师 / 直属领导 / 同事 / 朋友" focused={frame >= 8 && frame < 38}/>
        <Field label="你和对方现在是什么关系？" value={relation} placeholder="例如：合作顺畅，但平时联系不多" focused={frame >= 40 && frame < 70}/>
        <Field label="对方平时沟通习惯" value={habit} placeholder="例如：回复慢，比较严谨，喜欢有逻辑和证据" focused={frame >= 72 && frame < 110} multiline/>
        <Field label="可选：粘贴聊天记录" value={chat} placeholder="请保留说话人，并先删除姓名、电话等隐私信息。" focused={frame >= 110 && frame < 142} multiline/>
      </div>
      <p style={{padding: "0 2px", color: "#8B8D98", fontSize: 11, lineHeight: 1.45, margin: "14px 0"}}>* 隐私提示：请先删除姓名、电话、地址等敏感信息。Social Lab 只会生成一次模拟参数，不会联系真实人物。</p>
      <div style={{position: "relative", transform: `scale(${pressScale(frame, 158)})`}}><Button>{loading ? <><Spinner frame={frame}/> 正在生成画像...</> : <>生成 AI 扮演对象 <Icon name="arrow" size={18}/></>}</Button><AnchoredTap frame={frame} at={158}/></div>
    </div>
  </ProductShell>;
};

const Meter = ({label, description, value, frame, at}: Readonly<{label: string; description: string; value: number; frame: number; at: number}>) => (
  <div style={{background: "#F1F4F8", borderRadius: R.card, padding: 14, ...reveal(frame, at, 8)}}>
    <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 9, fontSize: 18, fontWeight: 800}}><span>{label}</span><span>{value}</span></div>
    <small style={{display: "block", color: C.muted, fontSize: 15, marginBottom: 8}}>{description}</small>
    <div style={{height: 8, borderRadius: 999, background: "#D9E0EA", overflow: "hidden"}}><div style={{height: "100%", width: `${interpolate(frame, [at, at + 24], [0, value], CLAMP)}%`, background: "#6F8F68", borderRadius: 999}}/></div>
  </div>
);

type MobilePersonaSceneProps = MobileSceneProps & Readonly<{
  exitProgress?: number;
}>;

const MobilePersonaScene = ({frame, exitProgress = 0}: MobilePersonaSceneProps) => {
  const buttonAt = 220;
  // Three contiguous eased segments: no dead zone in the middle and the final
  // position exposes the real bottom action instead of stopping above it.
  const scroll =
    smoothScroll(frame, 34, 92, 0, -188) +
    smoothScroll(frame, 92, 152, 0, -212) +
    smoothScroll(frame, 152, 208, 0, -172);
  const exitOpacity = 1 - exitProgress * 0.34;
  const exitShift = -18 * exitProgress;

  return <ProductShell step={3} contentStyle={{overflow: "hidden"}}>
    <div
      style={{
        position: "relative",
        height: "100%",
        opacity: exitOpacity,
        transform: `translateX(${exitShift}px)`,
        willChange: "transform, opacity",
      }}
    >
      <div style={{transform: `translateY(${scroll}px)`, willChange: "transform"}}>
        <div style={reveal(frame, 0)}><h2 style={{fontSize: 36, margin: "0 0 10px"}}>谨慎、重视证据的研究导师</h2><p style={{fontSize: 18, lineHeight: 1.65, color: C.muted, margin: "0 0 26px"}}>AI 将根据这个画像扮演对方。你在下一步中扮演自己，主动输入你想说的话。</p></div>
        <Card style={{padding: 22}}>
          <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16}}><span style={{fontSize: 20, fontWeight: 800}}>Persona Card</span><span style={{display: "inline-flex", alignItems: "center", gap: 5, minHeight: 34, padding: "0 10px", borderRadius: R.button, background: C.primarySoft, color: C.primary, fontSize: 13, fontWeight: 800}}><Icon name="sliders" size={15}/> 微调画像</span></div>
          <div style={{display: "grid", gridTemplateColumns: "1fr", gap: 12}}>{[
            ["沟通风格","理性、简洁，倾向先核对事实"],
            ["回复速度","通常较慢，但会认真阅读材料"],
            ["关注重点","证据是否充分、下一步是否可验证"],
            ["风险点","对模糊判断和没有依据的结论较敏感"],
          ].map(([a,b],i)=><div key={a} style={{minHeight: 76, borderRadius: R.card, padding: 16, background: i===3?C.social:C.lavender, ...reveal(frame, 12+i*6, 8)}}><small style={{display:"block", color:C.muted, fontSize:15, marginBottom:8}}>{a}</small><b style={{fontSize:15, fontWeight:400, lineHeight:1.35}}>{b}</b></div>)}</div>
        </Card>
        <Card style={{marginTop: 18}}><div style={{display:"flex", justifyContent:"space-between", marginBottom:16}}><span style={{fontSize:20,fontWeight:800}}>Relationship State</span><small style={{color:C.muted}}>模拟参数</small></div><div style={{display:"grid",gap:12}}><Meter label="信任" description="对你的判断基础" value={68} frame={frame} at={86}/><Meter label="耐心" description="继续解释的意愿" value={59} frame={frame} at={98}/><Meter label="开放度" description="接受新方向的程度" value={64} frame={frame} at={110}/></div></Card>
        <div style={{marginTop:18, padding:"0 2px", ...reveal(frame, 160, 10)}}><b style={{display:"block",fontSize:20,marginBottom:8}}>推荐策略</b><p style={{margin:0,lineHeight:1.5,color:C.muted}}>先简要说明阶段事实，再明确哪些判断仍不确定，最后提出一个具体、容易回应的验证请求。</p></div>
        <div style={{marginTop:22, paddingBottom:22, ...reveal(frame, 188, 8)}}>
          <div style={{position:"relative", transform:`scale(${pressScale(frame,buttonAt)})`}}>
            <Button>开始模拟对话 <Icon name="arrow" size={18}/></Button>
            <AnchoredTap frame={frame} at={buttonAt}/>
          </div>
        </div>
      </div>
    </div>
  </ProductShell>;
};

const Bubble = ({role, children, style}: Readonly<{role: "user"|"target"; children: ReactNode; style?: CSSProperties}>) => (
  <div style={{alignSelf: role === "user" ? "flex-end" : "flex-start", maxWidth: "82%", padding: "14px 16px", borderRadius: role === "user" ? "18px 18px 6px 18px" : "18px 18px 18px 6px", background: role === "user" ? C.accent : C.lavender, color: role === "user" ? C.accentInk : C.ink, fontSize: 15.5, lineHeight: 1.65, boxShadow: role === "user" ? "0 8px 18px rgba(177,229,93,0.18)" : S.soft, ...style}}>{children}</div>
);

const ChatHeader = () => <>
  <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",gap:16}}><div><h2 style={{fontSize:26,margin:"0 0 4px"}}>与研究导师模拟对话</h2><p style={{margin:0,color:C.muted,fontSize:14}}>当前态度：谨慎</p></div><SecondaryButton style={{minHeight:40,padding:"0 12px",fontSize:13}}><Icon name="refresh" size={16}/>重新开始</SecondaryButton></div>
  <div style={{margin:"10px 0 14px",width:"fit-content",maxWidth:"100%",padding:"10px 14px",background:C.primarySoft,color:C.primary,borderRadius:999,fontSize:13,lineHeight:1.4}}>对方目前关注：证据是否充分、下一步是否可验证</div>
</>;

const MessageSlot = ({
  visible,
  align,
  children,
}: Readonly<{
  visible: boolean;
  align: "user" | "target";
  children: ReactNode;
}>) => (
  <div
    style={{
      minHeight: align === "user" ? 72 : 94,
      display: "flex",
      justifyContent: align === "user" ? "flex-end" : "flex-start",
      alignItems: "flex-start",
      marginBottom: 8,
      opacity: visible ? 1 : 0,
      visibility: visible ? "visible" : "hidden",
      transform: `translateY(${visible ? 0 : 8}px)`,
    }}
  >
    {children}
  </div>
);

type MobileConversationSceneProps = MobileSceneProps & Readonly<{
  entryProgress?: number;
}>;

const MobileConversationScene = ({frame, entryProgress = 1}: MobileConversationSceneProps) => {
  const firstSendAt = 74;
  const secondSendAt = 274;
  const endAt = 382;
  const firstDraft = typeText(frame, 8, 68, "老师，我整理了目前的阶段结果，想先请您帮我判断方向是否合理。");
  const firstSent = frame >= firstSendAt;
  const firstTyping = frame >= 90 && frame < 152;
  const firstReply = frame >= 152;
  const secondDraft = typeText(frame, 190, 266, "我目前更倾向验证用户反馈与结果变化之间的关系，但证据还不完整。");
  const secondSent = frame >= secondSendAt;
  const secondTyping = frame >= 290 && frame < 348;
  const secondReply = frame >= 348;

  // Scroll only as much as is required by the newly appended message. The
  // previous turns remain visible, matching the real chat screen experience.
  const contentShift =
    smoothScroll(frame, 140, 166, 0, -10) +
    smoothScroll(frame, 260, 292, 0, -14) +
    smoothScroll(frame, 340, 372, 0, -18);
  const draft = !firstSent ? firstDraft : !secondSent ? secondDraft : "";
  const sendScale = pressScale(frame, firstSendAt) * pressScale(frame, secondSendAt);
  const endReady = frame >= 366;
  const endPressed = frame >= endAt;
  const estimatedCharsPerLine = 22;
  const draftLineCount = draft
    ? Math.min(3, Math.max(1, Math.ceil(draft.length / estimatedCharsPerLine)))
    : 1;
  const composerHeight = 46 + (draftLineCount - 1) * 19;

  return <div
    style={{
      position: "absolute",
      inset: 0,
      opacity: entryProgress,
      transform: `translateX(${(1 - entryProgress) * 28}px)`,
      willChange: "transform, opacity",
    }}
  >
    <ProductShell step={4} contentStyle={{overflow:"hidden"}}>
      <div style={{height:"100%",display:"flex",flexDirection:"column"}}>
        <ChatHeader/>
        <div style={{position: "relative", flex:1,minHeight:0,overflow:"hidden",padding:"4px 4px 8px"}}>
          <div style={{position:"absolute",left:4,right:4,top:0,transform:`translateY(${contentShift}px)`,willChange:"transform"}}>
            <MessageSlot visible={firstSent} align="user"><Bubble role="user">老师，我整理了目前的阶段结果，想先请您帮我判断方向是否合理。</Bubble></MessageSlot>
            <MessageSlot visible={firstTyping || firstReply} align="target">{firstReply ? <Bubble role="target">可以。先说你最确定的发现、依据，以及现在还不能确定的地方。</Bubble> : <p style={{margin:0,padding:"8px 2px",color:C.action,fontSize:14,fontWeight:800}}>对方正在输入中...</p>}</MessageSlot>
            <MessageSlot visible={secondSent} align="user"><Bubble role="user">我目前更倾向验证用户反馈与结果变化之间的关系，但证据还不完整。</Bubble></MessageSlot>
            <MessageSlot visible={secondTyping || secondReply} align="target">{secondReply ? <Bubble role="target">这个方向可以，但先不要把相关性写成结论。把证据和缺口列出来，再决定下一步实验。</Bubble> : <p style={{margin:0,padding:"8px 2px",color:C.action,fontSize:14,fontWeight:800}}>对方正在输入中...</p>}</MessageSlot>
          </div>
        </div>
        <div style={{display:"grid",gridTemplateColumns:"minmax(0,1fr) 46px",gap:10,padding:"10px 0 6px",alignItems:"end",opacity:endPressed?0.45:1}}>
          <div
            style={{
              minHeight: composerHeight,
              maxHeight: 84,
              borderRadius: 18,
              background: C.surface,
              border: `1px solid ${C.line}`,
              padding: draftLineCount > 1 ? "10px 16px" : "12px 16px",
              fontSize: 15,
              lineHeight: 1.45,
              boxShadow: S.soft,
              color: draft ? C.ink : C.faint,
              whiteSpace: "pre-wrap",
              overflowWrap: "anywhere",
              wordBreak: "break-word",
              overflow: "hidden",
              display: "flex",
              alignItems: draftLineCount > 1 ? "flex-start" : "center",
            }}
          >
            {draft || "输入下一句话..."}
          </div>
          <div style={{position:"relative",width:46,height:46,borderRadius:16,display:"grid",placeItems:"center",background:C.primary,color:"#FFF",boxShadow:S.send,transform:`scale(${sendScale})`}}><Icon name="send" size={20}/><AnchoredTap frame={frame} at={firstSendAt} color="#FFF"/><AnchoredTap frame={frame} at={secondSendAt} color="#FFF"/></div>
        </div>
        <div style={{position:"relative",transform:`scale(${pressScale(frame,endAt)})`}}>
          <SecondaryButton style={{width:"100%",marginTop:2,opacity:endReady?1:0.52,background:endPressed?C.primary:C.surface,color:endPressed?"#FFF":C.primary}}>结束模拟并查看分析</SecondaryButton>
          <AnchoredTap frame={frame} at={endAt} color={endPressed?"#FFF":C.primary}/>
        </div>
      </div>
    </ProductShell>
  </div>;
};

const REPORT_HANDOFF_FRAME = 18;
const REPORT_CONTINUITY_OFFSET = timeline.dynamics.duration - REPORT_HANDOFF_FRAME;

type AgentStageProps = Readonly<{
  frame: number;
  index: number;
  title: string;
  subtitle: string;
  start: number;
  end: number;
}>;

const AgentStage = ({frame, index, title, subtitle, start, end}: AgentStageProps) => {
  const active = frame >= start;
  const complete = frame >= end;
  const progress = interpolate(frame, [start, end], [0, 100], CLAMP);
  const cardOpacity = interpolate(frame, [start - 10, start + 8], [0.42, 1], CLAMP);
  const completionScale = interpolate(
    frame,
    [end, end + 3, end + 7, end + 12],
    [1, 1.018, 0.994, 1],
    CLAMP,
  );
  const completionLift = interpolate(
    frame,
    [end, end + 3, end + 7, end + 12],
    [0, -3, 1, 0],
    CLAMP,
  );
  return (
    <div
      style={{
        position: "relative",
        minHeight: 92,
        padding: "15px 14px 14px 54px",
        borderRadius: R.card,
        background: active ? C.surface : "#F8F9FC",
        border: `1px solid ${active ? C.selectedBorder : C.line}`,
        boxShadow: active ? S.soft : "none",
        opacity: cardOpacity,
        transform: `translateY(${completionLift}px) scale(${completionScale})`,
        transformOrigin: "center",
        willChange: "transform",
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 12,
          top: 20,
          width: 32,
          height: 32,
          borderRadius: 10,
          display: "grid",
          placeItems: "center",
          background: complete ? C.accent : active ? C.selected : C.neutralTrack,
          color: complete ? C.accentInk : active ? C.selectedInk : C.muted,
          fontSize: 16,
          fontWeight: 900,
          transform: `scale(${complete ? completionScale : 1})`,
        }}
      >
        {complete ? <Icon name="check" size={17}/> : index}
      </div>
      <b style={{display:"block",fontSize:17,lineHeight:1.2}}>{title}</b>
      <span style={{display:"block",marginTop:4,color:C.muted,fontSize:12.5,lineHeight:1.4}}>{subtitle}</span>
      <div style={{height:5,marginTop:13,borderRadius:999,overflow:"hidden",background:C.neutralTrack}}>
        <div style={{height:"100%",width:`${progress}%`,borderRadius:999,background:C.action}}/>
      </div>
    </div>
  );
};

const AgentMechanismContent = ({frame}: Readonly<{frame: number}>) => {
  const stages = [
    {title:"Persona Agent", subtitle:"还原对象的沟通偏好", start:18, end:58},
    {title:"Simulation Agent", subtitle:"生成符合画像的回应", start:58, end:104},
    {title:"State Agent", subtitle:"更新关系与对话状态", start:104, end:152},
    {title:"Prediction Agent", subtitle:"评估成功率和可能结果", start:152, end:214},
  ] as const;
  const done = frame >= 214;
  const doneBounce = interpolate(
    frame,
    [214, 218, 224, 232],
    [1, 1.032, 0.992, 1],
    CLAMP,
  );
  const doneLift = interpolate(
    frame,
    [214, 218, 224, 232],
    [0, -4, 1, 0],
    CLAMP,
  );
  return (
    <ProductShell
      step={4}
      subtitleOverride="分析中 · 回应是怎样生成的"
      contentStyle={{overflow:"hidden"}}
    >
      <div style={{height:"100%",display:"flex",flexDirection:"column"}}>
        <div style={{padding:"14px 16px",borderRadius:18,background:C.lavender,border:`1px solid ${C.borderSoft}`,...reveal(frame,0,8)}}>
          <span style={{display:"block",color:C.muted,fontSize:12,marginBottom:7}}>当前用户消息</span>
          <b style={{display:"block",fontSize:15.5,lineHeight:1.55}}>“我整理了目前的阶段结果，也想确认下一步应该优先推进什么。”</b>
        </div>
        <div style={{position:"relative",display:"grid",gap:10,marginTop:12,flex:1,minHeight:0}}>
          <div style={{position:"absolute",left:28,top:42,bottom:42,width:2,background:C.neutralTrack}}/>
          <div style={{position:"absolute",left:28,top:42,width:2,height:`${interpolate(frame,[18,214],[0,288],CLAMP)}px`,background:C.action}}/>
          {stages.map((stage,index)=><AgentStage key={stage.title} frame={frame} index={index+1} {...stage}/>) }
        </div>
        <div
          style={{
            minHeight: 38,
            marginTop: 10,
            borderRadius: 14,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: 8,
            background: done ? C.selected : C.primary,
            color: done ? C.selectedInk : "#FFF",
            fontSize: 13,
            fontWeight: 800,
            opacity: opacityIn(frame, 200, 14),
            transform: `translateY(${doneLift}px) scale(${doneBounce})`,
            boxShadow: done ? "0 10px 24px rgba(79,183,126,0.16)" : "none",
            willChange: "transform",
          }}
        >
          {done ? <><Icon name="check" size={16}/> 多Agent分析已完成</> : <><Spinner frame={frame} size={16}/> 正在汇总分析</>}
        </div>
      </div>
    </ProductShell>
  );
};

const MobileAgentMechanismScene = ({frame}: MobileSceneProps) => <AgentMechanismContent frame={frame}/>;

const Factor = ({tone,label,title,copy}: Readonly<{tone:string;label:string;title:string;copy:string}>) => <div style={{padding:14,borderRadius:R.card,background:C.surface,border:`1px solid ${C.line}`}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><span style={{padding:"5px 8px",borderRadius:999,background:tone,color:C.ink,fontSize:12,fontWeight:800}}>{label}</span><span style={{fontSize:12,color:C.muted}}>高影响</span></div><b style={{display:"block",fontSize:15,marginTop:10}}>{title}</b><p style={{fontSize:13,lineHeight:1.55,color:C.muted,margin:"6px 0 0"}}>{copy}</p></div>;

const RECOMMENDED_MESSAGE = "老师，我把目前的结果整理成了三部分：已观察到的发现、支持它的依据，以及仍不确定的地方。基于这些内容，我更倾向优先验证用户反馈与结果变化之间的关系。您觉得是否值得先做一个小范围实验？";

const MobileReportDocument = ({reportFrame}: Readonly<{reportFrame: number}>) => {
  const score = Math.round(interpolate(reportFrame, [0, 24], [72, 78], CLAMP));
  const scroll =
    smoothScroll(reportFrame, 58, 108, 0, -108) +
    smoothScroll(reportFrame, 116, 176, 0, -218);
  return <div style={{transform:`translateY(${scroll}px)`,display:"grid",gap:14,willChange:"transform"}}>
    <section style={{padding:20,borderRadius:24,background:"linear-gradient(135deg,#F0EDFF,#ECFFD2)",border:`1px solid ${C.borderSoft}`,boxShadow:S.card}}>
      <p style={{margin:0,color:C.muted,fontSize:13,fontWeight:800}}>本轮结果</p><div style={{display:"flex",alignItems:"baseline",gap:5,marginTop:8}}><strong style={{fontSize:72,lineHeight:1,color:C.primary}}>{score}</strong><span style={{color:C.muted}}>/ 100</span></div><span style={{display:"inline-flex",padding:"7px 10px",borderRadius:999,background:C.selected,color:C.selectedInk,fontSize:13,fontWeight:800}}>方向清晰，但证据表达仍可加强</span><p style={{fontSize:14,lineHeight:1.65,color:C.muted,margin:"14px 0 0"}}>你完成了两轮有效对话：先说明阶段判断，再主动承认证据缺口；如果能更早给出具体依据，对方会更容易判断下一步。</p>
    </section>
    <Card><div style={{display:"flex",justifyContent:"space-between",alignItems:"end",marginBottom:12}}><div><p style={{margin:0,fontSize:12,color:C.muted,fontWeight:800}}>关键判断</p><h3 style={{fontSize:20,margin:"3px 0 0"}}>最关键的三个影响</h3></div><span style={{fontSize:12,color:C.muted}}>已按影响程度筛选</span></div><div style={{display:"grid",gap:10}}><Factor tone={C.selected} label="正向" title="承认不确定性" copy="避免把阶段判断包装成结论，降低了对方的防御。"/><Factor tone={C.primarySoft} label="正向" title="请求具体" copy="将问题收敛为一个可回应的下一步，提升了沟通效率。"/><Factor tone={C.social} label="负向" title="证据出现较晚" copy="第一句话仍缺少具体结果，使对方需要继续追问。"/></div></Card>
    <Card style={{background:C.amber,borderColor:C.amberBorder,boxShadow:"none"}}><b style={{fontSize:15}}>推荐下一步</b><p style={{fontSize:14,lineHeight:1.6,color:"#695D45",margin:"8px 0 0"}}>先把现有结果按“发现—依据—不确定点”整理，再提出一个最值得优先验证的方向。</p></Card>
    <Card style={{background:C.lavender,borderColor:"#DFD9F4",boxShadow:"none"}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><span style={{fontSize:12,color:C.muted,fontWeight:800}}>AI 推荐写作</span><b style={{display:"block",fontSize:17,marginTop:3}}>把分析变成一条可继续发送的消息</b></div><div style={{width:40,height:40,borderRadius:14,display:"grid",placeItems:"center",background:C.primary,color:"#FFF"}}><Icon name="sparkle" size={19}/></div></div><p style={{background:C.surface,border:`1px solid ${C.line}`,borderRadius:18,padding:16,color:C.ink,fontSize:15,lineHeight:1.75,margin:"12px 0"}}>{RECOMMENDED_MESSAGE}</p><Button style={{minHeight:52,fontSize:16,background:C.accent,color:C.accentInk,boxShadow:"0 12px 24px rgba(177,229,93,0.22)"}}><Icon name="arrow" size={17}/>进入推荐写作</Button></Card>
  </div>;
};

const MobileReportHandoffScene = ({frame}: MobileSceneProps) => {
  const reportIn = interpolate(frame, [8, REPORT_HANDOFF_FRAME + 16], [0, 1], {...CLAMP, easing: EASE});
  const reportFrame = Math.max(0, frame - REPORT_HANDOFF_FRAME);
  return (
    <div style={{position:"absolute",inset:0,overflow:"hidden"}}>
      <div style={{position:"absolute",inset:0,opacity:1-reportIn,transform:`scale(${1-reportIn*0.018})`}}>
        <AgentMechanismContent frame={timeline.mechanism.duration}/>
      </div>
      <div style={{position:"absolute",inset:0,opacity:reportIn,transform:`translateX(${(1-reportIn)*30}px)`}}>
        <ProductShell step={5} contentStyle={{overflow:"hidden"}}>
          <MobileReportDocument reportFrame={reportFrame}/>
        </ProductShell>
      </div>
    </div>
  );
};

type RewriteStepProps = Readonly<{
  frame: number;
  at: number;
  index: string;
  title: string;
  copy: string;
  tone: string;
}>;

const RewriteStep = ({frame,at,index,title,copy,tone}: RewriteStepProps) => {
  const active = frame >= at;
  return <div style={{display:"grid",gridTemplateColumns:"36px 1fr",gap:12,alignItems:"start",padding:"12px 13px",borderRadius:17,background:active?tone:"rgba(255,255,255,0.58)",border:`1px solid ${active?C.borderSoft:C.line}`,opacity:interpolate(frame,[at-10,at],[0.42,1],CLAMP),transform:`translateX(${interpolate(frame,[at-10,at],[16,0],{...CLAMP,easing:EASE})}px)`}}><div style={{width:34,height:34,borderRadius:12,display:"grid",placeItems:"center",background:active?C.primary:C.neutralTrack,color:active?"#FFF":C.muted,fontSize:12,fontWeight:900}}>{active?<Icon name="check" size={15}/>:index}</div><div><b style={{display:"block",fontSize:14.5}}>{title}</b><span style={{display:"block",fontSize:12.2,lineHeight:1.48,color:C.muted,marginTop:3}}>{copy}</span></div></div>;
};

const MobileRewriteStudioScene = ({frame}: MobileSceneProps) => {
  const pullback = interpolate(frame,[0,24],[0,1],{...CLAMP,easing:EASE});
  const rewriteText = typeText(frame,82,146,RECOMMENDED_MESSAGE);
  const showControls = opacityIn(frame,148,14);
  const buttonAt = 196;
  const originalOpacity = interpolate(frame,[54,78],[1,0.42],CLAMP);
  return <ProductViewport>
    <div style={{position:"absolute",inset:0,overflow:"hidden",background:"radial-gradient(circle at 82% 8%,rgba(200,244,122,0.34),transparent 34%),linear-gradient(180deg,#E9EDF5 0%,#F4F1ED 58%,#EFEAFB 100%)",padding:22}}>
      <div style={{opacity:pullback,transform:`translateY(${(1-pullback)*12}px)`}}>
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between"}}><div><p style={{margin:"0 0 4px",fontSize:11.5,fontWeight:900,letterSpacing:"0.12em",color:C.primary}}>SOCIAL LAB · AI 推荐写作</p><h2 style={{fontSize:28,lineHeight:1.12,margin:0}}>把“知道问题”变成“说得更好”</h2></div><div style={{width:44,height:44,borderRadius:16,display:"grid",placeItems:"center",background:C.primary,color:"#FFF",boxShadow:S.send}}><Icon name="sparkle" size={21}/></div></div>
        <p style={{fontSize:13.5,lineHeight:1.55,color:C.muted,margin:"9px 0 0"}}>不是替你写一句漂亮话，而是重建事实、判断与请求的顺序。</p>
      </div>

      <div style={{position:"absolute",left:22,right:22,top:102,bottom:22,borderRadius:30,overflow:"hidden",background:C.page,border:`1px solid ${C.borderSoft}`,boxShadow:"0 26px 72px rgba(47,47,99,0.18)",transform:`scale(${interpolate(pullback,[0,1],[1.06,1])})`,transformOrigin:"top center"}}>
        <div style={{height:54,padding:"0 18px",display:"flex",alignItems:"center",justifyContent:"space-between",background:"rgba(255,255,255,0.92)",borderBottom:`1px solid ${C.borderSoft}`}}><div><b style={{fontSize:15}}>推荐写作工作台</b><span style={{display:"block",fontSize:11.5,color:C.muted,marginTop:2}}>基于本轮对话与报告生成</span></div><span style={{padding:"6px 9px",borderRadius:999,background:C.selected,color:C.selectedInk,fontSize:11.5,fontWeight:800}}>上下文已带入</span></div>

        <div style={{padding:16,display:"grid",gap:12}}>
          <div style={{display:"grid",gridTemplateColumns:"1fr 38px",gap:10,alignItems:"center",padding:14,borderRadius:19,background:C.surface,border:`1px solid ${C.line}`,opacity:originalOpacity}}><div><span style={{fontSize:11.5,color:C.muted,fontWeight:800}}>原表达</span><p style={{margin:"6px 0 0",fontSize:13.3,lineHeight:1.55}}>老师，我整理了目前的阶段结果，也想确认下一步应该优先推进什么。</p></div><div style={{width:36,height:36,borderRadius:13,display:"grid",placeItems:"center",background:C.social,color:C.danger,fontWeight:900}}>!</div></div>

          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8}}>
            {[{label:"判断过早",at:30},{label:"依据缺失",at:42},{label:"请求发散",at:54}].map((item)=><div key={item.label} style={{padding:"8px 5px",borderRadius:999,textAlign:"center",background:C.social,color:C.ink,border:`1px solid ${C.borderSoft}`,fontSize:11.5,fontWeight:800,opacity:opacityIn(frame,item.at,8),transform:`scale(${interpolate(frame,[item.at-6,item.at+6],[0.88,1],CLAMP)})`}}>{item.label}</div>)}
          </div>

          <div style={{display:"grid",gridTemplateColumns:"142px 1fr",gap:10,alignItems:"stretch"}}>
            <div style={{display:"grid",gap:7}}><RewriteStep frame={frame} at={66} index="01" title="原句诊断" copy="证据出现较晚，请求范围偏大" tone={C.work}/><RewriteStep frame={frame} at={84} index="02" title="改写重点" copy="先给事实，再明确判断边界" tone={C.lavender}/><RewriteStep frame={frame} at={102} index="03" title="预期变化" copy="让对方更容易给出明确反馈" tone={C.accentSoft}/></div>
            <div style={{position:"relative",minHeight:232,padding:15,borderRadius:20,background:C.lavender,border:"1px solid #DFD9F4",boxShadow:S.soft}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><span style={{fontSize:11.5,color:C.muted,fontWeight:800}}>推荐版本</span><span style={{fontSize:11,color:C.selectedInk,background:C.selected,padding:"5px 7px",borderRadius:999,fontWeight:800}}>AI 正在重构</span></div><p style={{margin:"12px 0 0",fontSize:13.2,lineHeight:1.63,color:C.ink,minHeight:166}}>{rewriteText}<span style={{opacity:frame>=82&&frame<146?1:0,color:C.primary}}>▍</span></p><div style={{position:"absolute",left:15,right:15,bottom:12,height:4,borderRadius:999,overflow:"hidden",background:C.neutralTrack}}><div style={{height:"100%",width:`${interpolate(frame,[82,146],[0,100],CLAMP)}%`,background:C.action,borderRadius:999}}/></div></div>
          </div>

          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:8,opacity:showControls}}>{[["其他表达","最小修改版"],["语气选择","更温和版"],["边界表达","更坚定版"]].map(([label,value],index)=><div key={label} style={{padding:"9px 10px",borderRadius:15,background:C.surface,border:`1px solid ${C.line}`,transform:`translateY(${riseIn(frame,150+index*5,8)}px)`}}><span style={{display:"block",fontSize:10.5,color:C.muted}}>{label}</span><b style={{display:"block",fontSize:12.5,marginTop:2}}>{value}</b></div>)}</div>

          <div style={{position:"relative",transform:`scale(${pressScale(frame,buttonAt)})`}}><Button style={{minHeight:52,fontSize:16,background:C.accent,color:C.accentInk,boxShadow:"0 12px 24px rgba(177,229,93,0.22)"}}><Icon name="chat" size={17}/>用推荐表达继续对话</Button><AnchoredTap frame={frame} at={buttonAt} color={C.accentInk}/></div>
        </div>
      </div>
    </div>
  </ProductViewport>;
};

const MetricChip = ({label,value,tone,frame,at}: Readonly<{label:string;value:string;tone:string;frame:number;at:number}>) => <div style={{padding:"10px 11px",borderRadius:16,background:tone,border:`1px solid ${C.borderSoft}`,opacity:opacityIn(frame,at,10),transform:`translateY(${riseIn(frame,at,10)}px)`}}><span style={{display:"block",fontSize:10.5,color:C.muted}}>{label}</span><b style={{display:"block",fontSize:16,marginTop:3,color:C.primary}}>{value}</b></div>;

const MobileContinueConversationScene = ({frame}: MobileSceneProps) => {
  const composerText = typeText(frame,8,46,RECOMMENDED_MESSAGE);
  const sendAt = 56;
  const sent = frame >= 64;
  const typing = frame >= 86 && frame < 122;
  const reply = frame >= 122;
  const score = Math.round(interpolate(frame,[146,176],[78,86],CLAMP));
  const pullback = interpolate(frame,[174,204],[0,1],{...CLAMP,easing:EASE});
  const chatShift = smoothScroll(frame,112,146,0,-46);
  const chatTop = interpolate(pullback,[0,1],[92,98]);
  const chatHeight = interpolate(pullback,[0,1],[438,356]);
  const resultTop = interpolate(pullback,[0,1],[538,468]);
  return <ProductViewport>
    <div style={{position:"absolute",inset:0,overflow:"hidden",background:"linear-gradient(180deg,#F4F1ED 0%,#EEF1F8 100%)"}}>
      <div style={{position:"absolute",left:18,right:18,top:12,opacity:opacityIn(frame,0,12),transform:`translateY(${(1-opacityIn(frame,0,12))*8}px)`}}>
        <p style={{margin:0,fontSize:10.5,fontWeight:900,letterSpacing:"0.11em",color:C.primary}}>REWRITE → RETRY</p>
        <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:10,marginTop:4}}>
          <h2 style={{fontSize:24,lineHeight:1.08,margin:0,whiteSpace:"nowrap"}}>推荐写作，直接进入下一轮</h2>
          <span style={{flex:"0 0 auto",padding:"5px 8px",borderRadius:999,background:C.selected,color:C.selectedInk,fontSize:10.5,fontWeight:800}}>场景与画像已保留</span>
        </div>
      </div>

      <div style={{position:"absolute",left:interpolate(pullback,[0,1],[14,24]),right:interpolate(pullback,[0,1],[14,24]),top:chatTop,height:chatHeight,borderRadius:interpolate(pullback,[0,1],[22,28]),overflow:"hidden",background:C.page,border:`1px solid ${C.borderSoft}`,boxShadow:"0 20px 56px rgba(47,47,99,0.14)"}}>
        <div style={{height:54,padding:"0 16px",display:"flex",alignItems:"center",justifyContent:"space-between",background:"rgba(255,255,255,0.96)",borderBottom:`1px solid ${C.borderSoft}`}}>
          <div style={{display:"flex",alignItems:"center",gap:9}}>
            <div style={{width:36,height:36,borderRadius:13,display:"grid",placeItems:"center",background:C.primary,color:"#FFF",fontWeight:900}}>导</div>
            <div><b style={{fontSize:14}}>研究导师</b><span style={{display:"block",fontSize:11,color:C.action,marginTop:1}}>重新模拟 · 推荐版本已带入</span></div>
          </div>
          <span style={{padding:"5px 8px",borderRadius:999,background:C.selected,color:C.selectedInk,fontSize:10.5,fontWeight:800}}>推荐草稿</span>
        </div>

        <div style={{position:"absolute",left:14,right:14,top:66,bottom:88,overflow:"hidden"}}>
          <div style={{display:"flex",flexDirection:"column",gap:10,transform:`translateY(${chatShift}px)`,willChange:"transform"}}>
            <div style={{opacity:sent?1:0,transform:`translateY(${sent?0:10}px)`}}><Bubble role="user">{RECOMMENDED_MESSAGE}</Bubble></div>
            <div style={{alignSelf:"flex-start",padding:"7px 11px",borderRadius:15,background:C.surface,border:`1px solid ${C.line}`,fontSize:12,color:C.action,fontWeight:800,opacity:typing?1:0,visibility:typing?"visible":"hidden"}}>对方正在输入中 ···</div>
            <div style={{opacity:reply?opacityIn(frame,122,12):0,transform:`translateY(${reply?riseIn(frame,122,10):10}px)`}}><Bubble role="target">这个版本更清楚。先把这三部分发给我，我会根据证据帮你判断哪项验证最值得先做。</Bubble></div>
          </div>
        </div>

        <div style={{position:"absolute",left:12,right:12,bottom:12,display:"grid",gridTemplateColumns:"1fr 44px",gap:8,alignItems:"end"}}>
          <div style={{height:64,overflow:"hidden",borderRadius:17,background:C.surface,border:`1px solid ${C.line}`,padding:"9px 12px",fontSize:11.8,lineHeight:1.38,color:sent?C.faint:C.ink,boxShadow:S.soft}}>{sent?"输入下一句话...":composerText}<span style={{opacity:frame>=8&&frame<46?1:0,color:C.primary}}>▍</span></div>
          <div style={{position:"relative",width:44,height:44,borderRadius:15,display:"grid",placeItems:"center",background:C.primary,color:"#FFF",boxShadow:S.send,transform:`scale(${pressScale(frame,sendAt)})`}}><Icon name="send" size={19}/><AnchoredTap frame={frame} at={sendAt} color="#FFF"/></div>
        </div>
      </div>

      <div style={{position:"absolute",left:22,right:22,top:resultTop,opacity:opacityIn(frame,144,12),transform:`translateY(${riseIn(frame,144,10)}px)`}}>
        <div style={{padding:"13px 14px",borderRadius:20,background:"rgba(255,255,255,0.97)",border:`1px solid ${C.borderSoft}`,boxShadow:S.card}}>
          <div style={{display:"flex",alignItems:"center",justifyContent:"space-between",gap:12}}>
            <div><span style={{fontSize:10.5,color:C.muted,fontWeight:800}}>推荐版本投入新一轮后 · 示意对比</span><b style={{display:"block",fontSize:15.5,marginTop:2}}>沟通结果即时更新</b></div>
            <div style={{display:"flex",alignItems:"baseline",gap:3}}><strong style={{fontSize:31,color:C.primary}}>{score}</strong><span style={{fontSize:10.5,color:C.muted}}>/100</span></div>
          </div>
          <div style={{display:"grid",gridTemplateColumns:"repeat(3,1fr)",gap:7,marginTop:9}}>
            <MetricChip label="回复意愿" value="+12" tone={C.accentSoft} frame={frame} at={150}/>
            <MetricChip label="关系温度" value="+4" tone={C.lavender} frame={frame} at={160}/>
            <MetricChip label="目标清晰度" value="+18" tone={C.work} frame={frame} at={170}/>
          </div>
        </div>
      </div>

      <div style={{position:"absolute",left:22,right:22,bottom:10,opacity:pullback,transform:`translateY(${(1-pullback)*10}px)`}}>
        <div style={{display:"grid",gridTemplateColumns:"1fr 22px 1fr 22px 1fr",gap:3,alignItems:"center"}}>
          {[{icon:"sparkle",label:"推荐写作"},{icon:"chat",label:"继续对话"},{icon:"report",label:"对比结果"}].map((item,index)=><div key={item.label} style={{display:"contents"}}><div style={{minHeight:50,borderRadius:16,display:"grid",placeItems:"center",alignContent:"center",gap:3,background:index===1?C.primary:C.surface,color:index===1?"#FFF":C.primary,border:`1px solid ${C.borderSoft}`,boxShadow:S.soft}}><Icon name={item.icon} size={15}/><b style={{fontSize:10.5}}>{item.label}</b></div>{index<2&&<div style={{display:"grid",placeItems:"center",color:C.muted}}><Icon name="arrow" size={13}/></div>}</div>)}
        </div>
        <p style={{textAlign:"center",fontSize:11.5,lineHeight:1.4,color:C.muted,margin:"6px 0 0"}}>推荐表达会直接成为下一轮模拟的起点。</p>
      </div>
    </div>
  </ProductViewport>;
};

const MobileOutroScene = ({frame}: MobileSceneProps) => {
  return <ProductViewport><div style={{position:"absolute",inset:0,background:C.primary,color:"#FFF",display:"flex",flexDirection:"column",alignItems:"center",justifyContent:"center",textAlign:"center",padding:"0 44px"}}><div style={{width:92,height:92,borderRadius:28,display:"grid",placeItems:"center",background:C.accent,color:C.primary,boxShadow:"0 24px 70px rgba(200,244,122,0.22)",fontSize:42,fontWeight:900,opacity:opacityIn(frame,6,18),transform:`scale(${interpolate(frame,[0,28],[0.76,1],{...CLAMP,easing:EASE})})`}}>S</div><h1 style={{fontSize:42,margin:"24px 0 8px",opacity:opacityIn(frame,18)}}>Social Lab</h1><p style={{fontSize:19,lineHeight:1.6,color:"rgba(255,255,255,0.68)",margin:0,opacity:opacityIn(frame,28)}}>先演练，再开口。</p><div style={{display:"flex",gap:8,marginTop:28,opacity:opacityIn(frame,38)}}>{["理解对象","预演对话","解释结果"].map(x=><span key={x} style={{padding:"8px 10px",borderRadius:999,background:"rgba(255,255,255,0.08)",border:"1px solid rgba(255,255,255,0.10)",fontSize:12}}>{x}</span>)}</div></div></ProductViewport>;
};

export type MobileProductDemoProps = Readonly<{
  audio?: ProductAudioTrackProps["settings"];
  bgm?: ProductBgmTrackProps["settings"];
}>;

type StableSceneSlotProps = Readonly<{
  active: boolean;
  children: ReactNode;
  zIndex?: number;
}>;

const StableSceneSlot = ({active, children, zIndex = 1}: StableSceneSlotProps) => (
  <div
    aria-hidden={!active}
    style={{
      position: "absolute",
      inset: 0,
      overflow: "hidden",
      opacity: active ? 1 : 0,
      visibility: active ? "visible" : "hidden",
      pointerEvents: active ? "auto" : "none",
      zIndex: active ? zIndex : 0,
    }}
  >
    {children}
  </div>
);

const getActiveSceneIndex = (frame: number): number => {
  if (frame < timeline.landing.from) return 0;
  if (frame < timeline.picker.from) return 1;
  if (frame < timeline.scenarioForm.from) return 2;
  if (frame < timeline.personSetup.from) return 3;
  if (frame < timeline.persona.from) return 4;
  if (frame < timeline.conversation.from) return 5;
  if (frame < timeline.mechanism.from) return 6;
  if (frame < timeline.dynamics.from) return 7;
  if (frame < timeline.report.from) return 8;
  if (frame < timeline.rewrite.from) return 9;
  if (frame < timeline.outro.from) return 10;
  return 11;
};

export const MobileProductDemo = ({audio, bgm}: MobileProductDemoProps) => {
  const frame = useCurrentFrame();
  const activeScene = getActiveSceneIndex(frame);
  const personaToConversation = interpolate(
    frame,
    [timeline.conversation.from - 12, timeline.conversation.from],
    [0, 1],
    CLAMP,
  );
  const conversationPreEntry =
    activeScene === 5 && frame >= timeline.conversation.from - 12;

  useLayoutEffect(() => {
    // Chrome/Edge page translation mutates text nodes outside React and can make
    // React 19 throw removeChild/insertBefore DOM ownership errors while scrubbing.
    // Mark both the document and the composition subtree as non-translatable.
    document.documentElement.lang = "zh-CN";
    document.documentElement.setAttribute("translate", "no");
    document.documentElement.classList.add("notranslate");
    document.body.setAttribute("translate", "no");
    document.body.classList.add("notranslate");
  }, []);

  return (
    <div
      className="notranslate"
      lang="zh-CN"
      translate="no"
      style={{position: "absolute", inset: 0, overflow: "hidden", background: C.page}}
    >
      <StableSceneSlot active={activeScene === 0}>
        <MobileIntroScene frame={frame - timeline.unsent.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 1}>
        <MobileLandingScene frame={frame - timeline.landing.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 2}>
        <MobilePickerScene frame={frame - timeline.picker.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 3}>
        <MobileScenarioFormScene frame={frame - timeline.scenarioForm.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 4}>
        <MobilePersonSetupScene frame={frame - timeline.personSetup.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 5}>
        <MobilePersonaScene
          frame={frame - timeline.persona.from}
          exitProgress={personaToConversation}
        />
      </StableSceneSlot>
      <StableSceneSlot
        active={activeScene === 6 || conversationPreEntry}
        zIndex={2}
      >
        <MobileConversationScene
          frame={Math.max(0, frame - timeline.conversation.from)}
          entryProgress={conversationPreEntry ? personaToConversation : 1}
        />
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 7}>
        <MobileAgentMechanismScene frame={frame - timeline.mechanism.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 8}>
        <MobileReportHandoffScene frame={frame - timeline.dynamics.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 9}>
        <MobileRewriteStudioScene frame={frame - timeline.report.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 10}>
        <MobileContinueConversationScene frame={frame - timeline.rewrite.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 11}>
        <MobileOutroScene frame={frame - timeline.outro.from}/>
      </StableSceneSlot>
      <ProductBgmTrack settings={bgm}/>
      <ProductAudioTrack settings={audio}/>
    </div>
  );
};
