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
}: Readonly<{
  step: number;
  children: ReactNode;
  contentStyle?: CSSProperties;
  hideNav?: boolean;
  overlay?: ReactNode;
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
              {step === 0 ? STEP_LABELS[0] : `Step ${step} / 5 · ${STEP_LABELS[step]}`}
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
const Skeleton = ({width = "100%", height = 14}: Readonly<{width?: number | string; height?: number}>) => (
  <div style={{width, height, borderRadius: 999, background: "linear-gradient(90deg,#ECEEF3,#F7F8FB,#ECEEF3)"}}/>
);

const LandingContent = ({frame, clickable = false}: Readonly<{frame: number; clickable?: boolean}>) => {
  const buttonAt = 78;
  const scenarios = [
    {icon: "cap", label: "导师", summary: "推荐信 / 催回复", bg: C.advisor, iconBg: C.advisorIcon},
    {icon: "briefcase", label: "职场", summary: "加薪 / 汇报", bg: C.work, iconBg: C.workIcon},
    {icon: "heart", label: "社交", summary: "道歉 / 拒绝", bg: C.social, iconBg: C.socialIcon},
  ];
  return <>
    <div style={{minHeight: 360, padding: "24px 28px", borderRadius: 32, background: C.surface, border: `1px solid ${C.borderSoft}`, boxShadow: S.card, display: "flex", flexDirection: "column", justifyContent: "center", ...reveal(frame, 0)}}>
      <div style={{width: "fit-content", padding: "8px 11px", borderRadius: 16, display: "inline-flex", alignItems: "center", gap: 7, background: C.lavender, color: C.primary, fontSize: 13, fontWeight: 800}}><Icon name="sparkle" size={15}/> AI 人际沟通预演</div>
      <h1 style={{margin: "18px 0 14px", fontSize: 42, lineHeight: 1.06, fontWeight: 800, letterSpacing: 0}}>先演练，<br/>再开口。</h1>
      <p style={{margin: 0, color: C.muted, fontSize: 16, lineHeight: 1.68}}>在真实沟通前，先和 AI 生成的关系数字分身练习一遍，预判风险，并获得更稳妥的表达方式。</p>
      <div style={{marginTop: 22, transform: `scale(${clickable ? pressScale(frame, buttonAt) : 1})`}}><Button>开始模拟 <Icon name="arrow" size={18}/></Button></div>
    </div>
    <div style={{marginTop: 30, marginBottom: 12, ...reveal(frame, 18)}}>
      <h2 style={{fontSize: 20, margin: 0}}>常见场景</h2>
      <p style={{fontSize: 14, color: C.muted, margin: "4px 0 0"}}>选择后会自动带入后续表单。</p>
    </div>
    <div style={{display: "grid", gridTemplateColumns: "repeat(3,1fr)", gap: 10}}>
      {scenarios.map((s, i) => <div key={s.label} style={{minHeight: 132, padding: 12, borderRadius: 22, border: `1px solid ${C.line}`, background: s.bg, ...reveal(frame, 24 + i * 5, 10)}}>
        <div style={{width: 42, height: 42, borderRadius: 14, display: "grid", placeItems: "center", background: s.iconBg, color: "#FFF"}}><Icon name={s.icon} size={20}/></div>
        <b style={{display: "block", fontSize: 17, marginTop: 12}}>{s.label}</b>
        <span style={{display: "block", color: "#5C6B80", fontSize: 12, lineHeight: 1.35, marginTop: 2}}>{s.summary}</span>
      </div>)}
    </div>
    {clickable && <Tap frame={frame} at={buttonAt} x={196} y={323}/>} 
  </>;
};

type MobileSceneProps = Readonly<{frame: number}>;

const MobileIntroScene = ({frame}: MobileSceneProps) => {
  return <ProductShell step={0}><LandingContent frame={frame}/></ProductShell>;
};

const MobileLandingScene = ({frame}: MobileSceneProps) => {
  return <ProductShell step={0}><LandingContent frame={frame} clickable/></ProductShell>;
};

const MobilePickerScene = ({frame}: MobileSceneProps) => {
  const open = opacityIn(frame, 10, 10);
  const selectAt = 103;
  const selected = frame >= selectAt;
  const modalScale = interpolate(frame, [8, 22], [0.94, 1], {...CLAMP, easing: EASE});
  const options = [
    {icon: "cap", title: "导师沟通", copy: "申请推荐信、催回复或讨论项目", bg: C.advisor, iconBg: C.advisorIcon},
    {icon: "briefcase", title: "职场沟通", copy: "汇报、边界、加薪或绩效反馈", bg: C.work, iconBg: C.workIcon},
    {icon: "heart", title: "社交沟通", copy: "道歉、拒绝、解释误会或修复关系", bg: C.social, iconBg: C.socialIcon},
  ];
  const overlay = (
    <div style={{position: "absolute", inset: 0, zIndex: 60, display: "grid", placeItems: "center", padding: 24, opacity: open}}>
      <div style={{position: "absolute", inset: 0, background: "rgba(20,22,34,0.58)"}}/>
      <div style={{position: "relative", width: "100%", padding: "44px 20px 20px", borderRadius: 30, background: "#15182B", color: "#FFF", boxShadow: "0 24px 70px rgba(14,16,26,0.38)", transform: `scale(${modalScale})`}}>
        <div style={{position: "absolute", left: "50%", top: -25, transform: "translateX(-50%) rotate(-5deg)", width: "max-content", padding: "10px 20px", borderRadius: 999, background: "#FFF05B", color: "#081122", fontSize: 20, fontWeight: 900}}>选择你的沟通场景</div>
        <div style={{display: "grid", gap: 10}}>
          {options.map((o, i) => <div key={o.title} style={{minHeight: 112, padding: 14, borderRadius: 18, display: "grid", gridTemplateColumns: "48px 1fr 22px", gap: 13, alignItems: "center", background: selected && i === 0 ? C.selected : o.bg, color: "#081122", border: selected && i === 0 ? `2px solid ${C.selectedBorder}` : "2px solid transparent", ...reveal(frame, 22 + i * 7, 12)}}>
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
  return <ProductShell step={0} overlay={overlay}><LandingContent frame={frame}/></ProductShell>;
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
  const scroll = interpolate(frame, [0, 85, 160, 225], [0, 0, -255, -510], {...CLAMP, easing: EASE});
  const chosenTask = frame >= 34;
  const chosenUrgency = frame >= 94;
  const outcome = typeText(frame, 126, 169, "希望导师确认下一步，并指出最需要优先验证的方向。");
  const concern = frame >= 190;
  return <ProductShell step={1} contentStyle={{overflow: "hidden"}}>
    <div style={{transform: `translateY(${scroll}px)`}}>
      <div style={reveal(frame, 0)}><h2 style={{fontSize: 34, lineHeight: 1.12, margin: "0 0 10px"}}>这次你想解决什么沟通问题？</h2><p style={{fontSize: 17, lineHeight: 1.7, color: C.muted, margin: "0 0 26px"}}>先描述这次沟通任务，下一步再补充对方是谁。</p></div>
      <div style={{display: "grid", gap: 18}}>
        <QuestionCard number={1} title="这次你想沟通什么？" hint="单选 + 自定义 · 可跳过" complete={chosenTask}>
          <div style={{display: "flex", flexWrap: "wrap", gap: "10px 12px", marginBottom: 16}}>{["申请推荐信","催回复","申请延期","预约沟通"].map((x) => <Chip key={x} selected={chosenTask && x === "催回复"}>{x}</Chip>)}</div>
          <div style={{padding: "14px 16px", borderRadius: R.input, background: "#FBFAF7", color: chosenTask ? C.ink : C.faint, fontSize: 14}}>{chosenTask ? "想请导师确认项目的下一步方向" : "例如：我想请导师帮我写推荐信"}</div>
        </QuestionCard>
        <QuestionCard number={2} title="这件事有多紧急？" hint="单选 · 可跳过" complete={chosenUrgency}>
          <div style={{display: "flex", flexWrap: "wrap", gap: "10px 12px"}}>{["不着急，只是提前沟通","一周内需要回复","三天内需要回复"].map((x) => <Chip key={x} selected={chosenUrgency && x === "一周内需要回复"}>{x}</Chip>)}</div>
        </QuestionCard>
        <QuestionCard number={3} title="你希望这次沟通达到什么结果？" hint="文本输入，可选 · 可跳过" complete={outcome.length > 8}>
          <div style={{minHeight: 92, padding: "14px 16px", borderRadius: R.input, background: "#FBFAF7", color: outcome ? C.ink : C.faint, fontSize: 14, lineHeight: 1.6}}>{outcome || "例如：希望导师愿意帮我写推荐信，并且不要觉得我太唐突。"}</div>
        </QuestionCard>
        <QuestionCard number={4} title="你最担心哪里出问题？" hint="多选 + 可自定义 · 可跳过" complete={concern}>
          <div style={{display: "flex", flexWrap: "wrap", gap: "10px 12px"}}>{["担心显得不够配合","担心请求被拒绝","担心影响之后评价"].map((x) => <Chip key={x} selected={concern && x === "担心对方不认真听"}>{x}</Chip>)}<Chip selected={concern}>担心对方不认真听</Chip></div>
        </QuestionCard>
        <div style={{paddingBottom: 24, transform: `scale(${pressScale(frame, 218)})`}}><Button>继续补充对方信息 <Icon name="arrow" size={18}/></Button></div>
      </div>
    </div>
    <Tap frame={frame} at={32} x={108} y={280}/><Tap frame={frame} at={92} x={138} y={452}/><Tap frame={frame} at={218} x={197} y={555}/>
  </ProductShell>;
};

const MobilePersonSetupScene = ({frame}: MobileSceneProps) => {
  const scroll = interpolate(frame, [0, 80, 145, 178], [0, -120, -330, -430], {...CLAMP, easing: EASE});
  const role = typeText(frame, 14, 42, "研究导师");
  const relation = typeText(frame, 48, 76, "合作顺畅，但平时联系不多");
  const habit = typeText(frame, 84, 120, "回复慢，比较严谨，喜欢有逻辑和证据");
  const chat = typeText(frame, 124, 148, "我：老师，想确认下一步。\n导师：请先整理阶段结果。");
  const loading = frame >= 158;
  return <ProductShell step={2} contentStyle={{overflow: "hidden"}}>
    <div style={{transform: `translateY(${scroll}px)`}}>
      <div style={reveal(frame, 0)}><h2 style={{fontSize: 30, margin: "0 0 8px"}}>你希望 AI 扮演谁？</h2><p style={{fontSize: 17, lineHeight: 1.7, color: C.muted, margin: "0 0 18px"}}>请补充对方的信息。你将在后续对话中扮演自己，AI 会扮演这个沟通对象。</p></div>
      <div style={{display: "grid", gap: 14}}>
        <Field label="你想让 AI 扮演谁？" value={role} placeholder="例如：导师 / 直属领导 / 同事 / 朋友" focused={frame >= 12 && frame < 44}/>
        <Field label="你和对方现在是什么关系？" value={relation} placeholder="例如：合作顺畅，但平时联系不多" focused={frame >= 46 && frame < 78}/>
        <Field label="对方平时沟通习惯" value={habit} placeholder="例如：回复慢，比较严谨，喜欢有逻辑和证据" focused={frame >= 82 && frame < 122} multiline/>
        <Field label="可选：粘贴聊天记录" value={chat} placeholder="请保留说话人，并先删除姓名、电话等隐私信息。" focused={frame >= 122 && frame < 150} multiline/>
      </div>
      <p style={{padding: "0 2px", color: "#8B8D98", fontSize: 11, lineHeight: 1.45, margin: "14px 0"}}>* 隐私提示：请先删除姓名、电话、地址等敏感信息。Social Lab 只会生成一次模拟参数，不会联系真实人物。</p>
      <div style={{transform: `scale(${pressScale(frame, 155)})`}}><Button>{loading ? <><Spinner frame={frame}/> 正在生成画像...</> : <>生成 AI 扮演对象 <Icon name="arrow" size={18}/></>}</Button></div>
    </div>
    <Tap frame={frame} at={155} x={197} y={555}/>
  </ProductShell>;
};

const Meter = ({label, description, value, frame, at}: Readonly<{label: string; description: string; value: number; frame: number; at: number}>) => (
  <div style={{background: "#F1F4F8", borderRadius: R.card, padding: 14, ...reveal(frame, at, 8)}}>
    <div style={{display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 9, fontSize: 18, fontWeight: 800}}><span>{label}</span><span>{value}</span></div>
    <small style={{display: "block", color: C.muted, fontSize: 15, marginBottom: 8}}>{description}</small>
    <div style={{height: 8, borderRadius: 999, background: "#D9E0EA", overflow: "hidden"}}><div style={{height: "100%", width: `${interpolate(frame, [at, at + 24], [0, value], CLAMP)}%`, background: "#6F8F68", borderRadius: 999}}/></div>
  </div>
);

const MobilePersonaScene = ({frame}: MobileSceneProps) => {
  const scroll = interpolate(frame, [0, 100, 175, 232], [0, 0, -235, -435], {...CLAMP, easing: EASE});
  return <ProductShell step={3} contentStyle={{overflow: "hidden"}}>
    <div style={{transform: `translateY(${scroll}px)`}}>
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
      <div style={{marginTop:18, padding:"0 2px"}}><b style={{display:"block",fontSize:20,marginBottom:8}}>推荐策略</b><p style={{margin:0,lineHeight:1.5,color:C.muted}}>先简要说明阶段事实，再明确哪些判断仍不确定，最后提出一个具体、容易回应的验证请求。</p></div>
      <div style={{marginTop:22, paddingBottom:22, transform:`scale(${pressScale(frame,220)})`}}><Button>开始模拟对话 <Icon name="arrow" size={18}/></Button></div>
    </div>
    <Tap frame={frame} at={220} x={197} y={548}/>
  </ProductShell>;
};

const Bubble = ({role, children, style}: Readonly<{role: "user"|"target"; children: ReactNode; style?: CSSProperties}>) => (
  <div style={{alignSelf: role === "user" ? "flex-end" : "flex-start", maxWidth: "82%", padding: "14px 16px", borderRadius: role === "user" ? "18px 18px 6px 18px" : "18px 18px 18px 6px", background: role === "user" ? C.accent : C.lavender, color: role === "user" ? C.accentInk : C.ink, fontSize: 15.5, lineHeight: 1.65, boxShadow: role === "user" ? "0 8px 18px rgba(177,229,93,0.18)" : S.soft, ...style}}>{children}</div>
);

const ChatHeader = () => <>
  <div style={{display:"flex",justifyContent:"space-between",alignItems:"start",gap:16}}><div><h2 style={{fontSize:26,margin:"0 0 4px"}}>与研究导师模拟对话</h2><p style={{margin:0,color:C.muted,fontSize:14}}>当前态度：谨慎</p></div><SecondaryButton style={{minHeight:40,padding:"0 12px",fontSize:13}}><Icon name="refresh" size={16}/>重新开始</SecondaryButton></div>
  <div style={{margin:"10px 0 14px",width:"fit-content",maxWidth:"100%",padding:"10px 14px",background:C.primarySoft,color:C.primary,borderRadius:999,fontSize:13,lineHeight:1.4}}>对方目前关注：证据是否充分、下一步是否可验证</div>
</>;

const MobileConversationScene = ({frame}: MobileSceneProps) => {
  const draft = typeText(frame, 66, 116, "老师，我整理了目前的阶段结果，也想确认下一步应该优先推进什么。");
  const sent = frame >= 126;
  const typing = frame >= 142 && frame < 190;
  const reply = frame >= 188;
  const contentShift = interpolate(frame,[125,195],[0,-62],CLAMP);
  return <ProductShell step={4} contentStyle={{overflow:"hidden"}}>
    <div style={{height:"100%",display:"flex",flexDirection:"column"}}>
      <ChatHeader/>
      <div style={{flex:1,minHeight:0,display:"flex",flexDirection:"column",gap:18,padding:"8px 4px 14px",transform:`translateY(${contentShift}px)`}}>
        <Bubble role="target">我看过你目前的材料。先说说你最确定的判断，以及它来自哪些结果。</Bubble>
        <Bubble role="user">老师，我整理了目前的阶段结果，也想确认下一步应该优先推进什么。</Bubble>
        <Bubble role="target">可以。请先把阶段结果按“发现—依据—不确定点”整理，再告诉我你认为最值得优先验证的一个方向。</Bubble>
        <div style={{display: sent ? "contents" : "none"}}><Bubble role="user" style={reveal(frame,126,10)}>我目前更倾向于验证用户反馈与结果变化之间的关系，但证据还不完整。</Bubble></div>
        <p style={{display: typing ? "block" : "none",alignSelf:"flex-start",margin:0,padding:"6px 2px",color:C.action,fontSize:14,fontWeight:800}}>对方正在输入中...</p>
        <div style={{display: reply ? "contents" : "none"}}><Bubble role="target" style={reveal(frame,188,10)}>这个方向可以，但先不要把相关性写成结论。把现有证据和缺口列出来，我们再决定下一步实验。</Bubble></div>
      </div>
      <div style={{display:"grid",gridTemplateColumns:"1fr 46px",gap:10,padding:"10px 0 6px"}}>
        <div style={{minHeight:46,borderRadius:18,background:C.surface,border:`1px solid ${C.line}`,padding:"12px 16px",fontSize:15,boxShadow:S.soft,color:draft?C.ink:C.faint,whiteSpace:"nowrap",overflow:"hidden"}}>{sent?"输入下一句话...":draft||"输入下一句话..."}</div>
        <div style={{width:46,height:46,borderRadius:16,display:"grid",placeItems:"center",background:C.primary,color:"#FFF",boxShadow:S.send,transform:`scale(${pressScale(frame,122)})`}}><Icon name="send" size={20}/></div>
      </div>
      <SecondaryButton style={{width:"100%",marginTop:2}}>结束模拟并查看分析</SecondaryButton>
    </div>
    <Tap frame={frame} at={122} x={371} y={520}/>
  </ProductShell>;
};

const MobileAnalysisLoadingScene = ({frame}: MobileSceneProps) => {
  const tapped = frame >= 24;
  const progress = interpolate(frame,[36,220],[8,96],CLAMP);
  const stage = frame < 90 ? "正在整理对话轮次" : frame < 155 ? "正在生成沟通报告" : "正在准备推荐改写";
  return <ProductShell step={4}>
    <div style={{height:"100%",display:"flex",flexDirection:"column"}}>
      <ChatHeader/>
      <div style={{flex:1,display:"flex",flexDirection:"column",gap:18,padding:"8px 4px 14px",opacity:tapped?0.52:1}}>
        <Bubble role="target">这个方向可以，但先不要把相关性写成结论。把现有证据和缺口列出来，我们再决定下一步实验。</Bubble>
        <Bubble role="user">明白，我会先整理证据与不确定点，再提出一个可验证的方向。</Bubble>
      </div>
      <SecondaryButton style={{width:"100%",marginTop:2,background:tapped?C.primary:C.surface,color:tapped?"#FFF":C.primary,transform:`scale(${pressScale(frame,22)})`}}><><span style={{display: tapped ? "inline-flex" : "none",alignItems:"center",gap:8}}><Spinner frame={frame}/>正在生成分析...</span><span style={{display: tapped ? "none" : "inline"}}>结束模拟并查看分析</span></></SecondaryButton>
    </div>
    <Tap frame={frame} at={22} x={197} y={548}/>
    <div aria-hidden={!tapped} style={{position:"absolute",left:18,right:18,top:198,bottom:92,zIndex:65,display:tapped?"grid":"none",placeItems:"center",background:"rgba(244,241,237,0.80)"}}>
      <Card style={{width:"100%",padding:24,textAlign:"center",...reveal(frame,30,12)}}>
        <div style={{width:54,height:54,borderRadius:18,display:"grid",placeItems:"center",margin:"0 auto",background:C.primary,color:"#FFF"}}><div style={{transform:`rotate(${frame*8}deg)`}}><Icon name="brain" size={26}/></div></div>
        <h3 style={{fontSize:20,margin:"18px 0 6px"}}>{stage}</h3>
        <p style={{fontSize:14,lineHeight:1.6,color:C.muted,margin:"0 0 18px"}}>Social Lab 正在根据本轮真实对话生成结果，不会联系真实人物。</p>
        <div style={{height:8,borderRadius:999,background:C.neutralTrack,overflow:"hidden"}}><div style={{height:"100%",width:`${progress}%`,borderRadius:999,background:C.action}}/></div>
      </Card>
    </div>
  </ProductShell>;
};

const MobileReportLoadingScene = ({frame}: MobileSceneProps) => {
  const ready = frame >= 122;
  const contentOpacity = interpolate(frame,[118,145],[0,1],CLAMP);
  return <ProductShell step={5}>
    <div style={{display:"grid",gap:14}}>
      <div style={{padding:20,borderRadius:24,background:"linear-gradient(135deg,#F0EDFF,#ECFFD2)",border:`1px solid ${C.borderSoft}`,boxShadow:S.card}}>
        <><div style={{display:ready?"block":"none",opacity:contentOpacity}}><p style={{margin:0,color:C.muted,fontSize:13,fontWeight:800}}>本轮结果</p><div style={{display:"flex",alignItems:"baseline",gap:5,marginTop:8}}><strong style={{fontSize:72,lineHeight:1,color:C.primary}}>78</strong><span style={{color:C.muted}}>/ 100</span></div><span style={{display:"inline-flex",padding:"7px 10px",borderRadius:999,background:C.selected,color:C.selectedInk,fontSize:13,fontWeight:800}}>方向清晰，但证据表达仍可加强</span></div><div style={{display:ready?"none":"grid",gap:14}}><Skeleton width={92}/><Skeleton width={150} height={58}/><Skeleton width={220} height={28}/></div></>
      </div>
      <Card><><div style={{display:ready?"block":"none",opacity:contentOpacity}}><p style={{margin:"0 0 5px",fontSize:12,color:C.muted,fontWeight:800}}>关键判断</p><h3 style={{fontSize:20,margin:"0 0 14px"}}>最关键的三个影响</h3>{["主动说明不确定点，降低了过度承诺风险","请求足够具体，对方容易给出下一步","前半段事实依据仍然偏少"].map((x,i)=><div key={x} style={{padding:"12px 0",borderTop:i?`1px solid ${C.line}`:"none",fontSize:14,lineHeight:1.55}}>{x}</div>)}</div><div style={{display:ready?"none":"grid",gap:14}}><Skeleton width={110}/><Skeleton height={22}/><Skeleton/><Skeleton/><Skeleton/></div></></Card>
      <Card style={{background:C.amber,borderColor:C.amberBorder,boxShadow:"none"}}><><div style={{display:ready?"block":"none",opacity:contentOpacity}}><b style={{fontSize:15}}>推荐下一步</b><p style={{fontSize:14,lineHeight:1.6,color:"#695D45",margin:"8px 0 0"}}>先把现有结果按“发现—依据—不确定点”整理，再提出一个最值得优先验证的方向。</p></div><div style={{display:ready?"none":"grid",gap:12}}><Skeleton width={92}/><Skeleton/><Skeleton width="78%"/></div></></Card>
    </div>
  </ProductShell>;
};

const Factor = ({tone,label,title,copy}: Readonly<{tone:string;label:string;title:string;copy:string}>) => <div style={{padding:14,borderRadius:R.card,background:C.surface,border:`1px solid ${C.line}`}}><div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><span style={{padding:"5px 8px",borderRadius:999,background:tone,color:C.ink,fontSize:12,fontWeight:800}}>{label}</span><span style={{fontSize:12,color:C.muted}}>高影响</span></div><b style={{display:"block",fontSize:15,marginTop:10}}>{title}</b><p style={{fontSize:13,lineHeight:1.55,color:C.muted,margin:"6px 0 0"}}>{copy}</p></div>;

const MobileReportScene = ({frame}: MobileSceneProps) => {
  const scroll = interpolate(frame,[0,110,210,265],[0,-90,-300,-470],{...CLAMP,easing:EASE});
  return <ProductShell step={5} contentStyle={{overflow:"hidden"}}>
    <div style={{transform:`translateY(${scroll}px)`,display:"grid",gap:14}}>
      <section style={{padding:20,borderRadius:24,background:"linear-gradient(135deg,#F0EDFF,#ECFFD2)",border:`1px solid ${C.borderSoft}`,boxShadow:S.card,...reveal(frame,0)}}>
        <p style={{margin:0,color:C.muted,fontSize:13,fontWeight:800}}>本轮结果</p><div style={{display:"flex",alignItems:"baseline",gap:5,marginTop:8}}><strong style={{fontSize:72,lineHeight:1,color:C.primary}}>78</strong><span style={{color:C.muted}}>/ 100</span></div><span style={{display:"inline-flex",padding:"7px 10px",borderRadius:999,background:C.selected,color:C.selectedInk,fontSize:13,fontWeight:800}}>方向清晰，但证据表达仍可加强</span><p style={{fontSize:14,lineHeight:1.65,color:C.muted,margin:"14px 0 0"}}>你主动标出了不确定点，也提出了明确请求；如果能更早给出具体依据，对方会更容易判断下一步。</p>
      </section>
      <Card><div style={{display:"flex",justifyContent:"space-between",alignItems:"end",marginBottom:12}}><div><p style={{margin:0,fontSize:12,color:C.muted,fontWeight:800}}>关键判断</p><h3 style={{fontSize:20,margin:"3px 0 0"}}>最关键的三个影响</h3></div><span style={{fontSize:12,color:C.muted}}>已按影响程度筛选</span></div><div style={{display:"grid",gap:10}}><Factor tone={C.selected} label="正向" title="承认不确定性" copy="避免把阶段判断包装成结论，降低了对方的防御。"/><Factor tone={C.primarySoft} label="正向" title="请求具体" copy="将问题收敛为一个可回应的下一步，提升了沟通效率。"/><Factor tone={C.social} label="负向" title="证据出现较晚" copy="前半段缺少具体数据，使对方需要额外追问。"/></div></Card>
      <Card style={{background:C.amber,borderColor:C.amberBorder,boxShadow:"none"}}><b style={{fontSize:15}}>推荐下一步</b><p style={{fontSize:14,lineHeight:1.6,color:"#695D45",margin:"8px 0 0"}}>先把现有结果按“发现—依据—不确定点”整理，再提出一个最值得优先验证的方向。</p><div style={{display:"grid",gap:10,marginTop:14}}><Button style={{minHeight:52,fontSize:16,background:C.accent,color:C.accentInk,boxShadow:"0 12px 24px rgba(177,229,93,0.22)"}}><Icon name="refresh" size={17}/>用推荐版本重新模拟</Button><SecondaryButton>查看完整分析 <Icon name="chevron" size={17}/></SecondaryButton></div></Card>
      <Card style={{background:C.lavender,borderColor:"#DFD9F4",boxShadow:"none"}}><b style={{fontSize:16}}>推荐改写</b><p style={{background:C.surface,border:`1px solid ${C.line}`,borderRadius:18,padding:16,color:C.ink,fontSize:15,lineHeight:1.75,margin:"12px 0"}}>老师，我把目前的结果整理成了三部分：已观察到的发现、支持它的依据，以及仍不确定的地方。基于这些内容，我目前更倾向优先验证用户反馈与结果变化之间的关系。您觉得这个方向是否值得先做一个小范围实验？</p><SecondaryButton><Icon name="copy" size={16}/>复制优化表达</SecondaryButton></Card>
    </div>
  </ProductShell>;
};

const MobileRewriteScene = ({frame}: MobileSceneProps) => {
  const copied = frame >= 46 && frame < 88;
  const retry = frame >= 104;
  return <ProductShell step={5}>
    <div style={{display:"grid",gap:14}}>
      <Card style={{background:C.lavender,borderColor:"#DFD9F4",boxShadow:"none",...reveal(frame,0)}}>
        <div style={{display:"flex",justifyContent:"space-between",alignItems:"center"}}><div><p style={{margin:0,fontSize:12,color:C.muted,fontWeight:800}}>推荐改写</p><h3 style={{fontSize:20,margin:"3px 0 0"}}>更容易得到明确回复的表达</h3></div><div style={{width:42,height:42,borderRadius:14,display:"grid",placeItems:"center",background:C.primary,color:"#FFF"}}><Icon name="sparkle" size={20}/></div></div>
        <p style={{background:C.surface,border:`1px solid ${C.line}`,borderRadius:18,padding:16,color:C.ink,fontSize:15,lineHeight:1.75,margin:"16px 0"}}>老师，我把目前的结果整理成了三部分：已观察到的发现、支持它的依据，以及仍不确定的地方。基于这些内容，我目前更倾向优先验证用户反馈与结果变化之间的关系。您觉得这个方向是否值得先做一个小范围实验？</p>
        <div style={{display:"grid",gap:10}}><SecondaryButton style={{transform:`scale(${pressScale(frame,42)})`}}><Icon name="copy" size={16}/>复制优化表达</SecondaryButton><Button style={{minHeight:56,fontSize:16,background:C.accent,color:C.accentInk,boxShadow:"0 12px 24px rgba(177,229,93,0.22)",transform:`scale(${pressScale(frame,100)})`}}><><span style={{display:retry?"inline-flex":"none",alignItems:"center",gap:8}}><Spinner frame={frame}/>正在重新模拟...</span><span style={{display:retry?"none":"inline-flex",alignItems:"center",gap:8}}><Icon name="refresh" size={17}/>用推荐版本重新模拟</span></></Button></div>
      </Card>
      <Card><b style={{fontSize:15}}>为什么这样改</b><div style={{display:"grid",gap:10,marginTop:12}}>{[["事实","先交代已观察到的结果"],["判断","明确这是倾向，而不是定论"],["请求","把问题收敛成可回答的验证方向"]].map(([a,b],i)=><div key={a} style={{display:"grid",gridTemplateColumns:"54px 1fr",gap:10,padding:12,borderRadius:R.card,background:i===0?C.work:i===1?C.primarySoft:C.accentSoft}}><b style={{fontSize:13}}>{a}</b><span style={{fontSize:13,lineHeight:1.5,color:C.muted}}>{b}</span></div>)}</div></Card>
    </div>
    <Tap frame={frame} at={42} x={214} y={425}/><Tap frame={frame} at={100} x={214} y={488} color={C.accentInk}/>
    <div aria-hidden={!copied} style={{position:"absolute",left:"50%",top:"50%",transform:"translate(-50%,-50%)",width:280,padding:"14px 18px",borderRadius:16,textAlign:"center",background:C.ink,color:"#FFF",fontSize:14,lineHeight:1.55,boxShadow:S.toast,zIndex:80,display:copied?"block":"none",...reveal(frame,48,8)}}>已复制优化表达。</div>
  </ProductShell>;
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
}>;

const StableSceneSlot = ({active, children}: StableSceneSlotProps) => (
  <div
    aria-hidden={!active}
    style={{
      position: "absolute",
      inset: 0,
      overflow: "hidden",
      opacity: active ? 1 : 0,
      visibility: active ? "visible" : "hidden",
      pointerEvents: active ? "auto" : "none",
      zIndex: active ? 1 : 0,
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
        <MobilePersonaScene frame={frame - timeline.persona.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 6}>
        <MobileConversationScene frame={frame - timeline.conversation.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 7}>
        <MobileAnalysisLoadingScene frame={frame - timeline.mechanism.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 8}>
        <MobileReportLoadingScene frame={frame - timeline.dynamics.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 9}>
        <MobileReportScene frame={frame - timeline.report.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 10}>
        <MobileRewriteScene frame={frame - timeline.rewrite.from}/>
      </StableSceneSlot>
      <StableSceneSlot active={activeScene === 11}>
        <MobileOutroScene frame={frame - timeline.outro.from}/>
      </StableSceneSlot>
      <ProductBgmTrack settings={bgm}/>
      <ProductAudioTrack settings={audio}/>
    </div>
  );
};
