import {ArrowRight, RotateCcw} from "lucide-react";

import {COLORS, RADII, TYPOGRAPHY} from "../../design/tokens";

export type ActionPanelProps = {
  text: string;
  revealProgress?: number;
};

export const ActionPanel = ({text, revealProgress = 1}: ActionPanelProps) => {
  const reveal = Math.max(0, Math.min(1, revealProgress));

  return (
    <section
      style={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 28,
        boxSizing: "border-box",
        padding: "24px 26px",
        borderRadius: RADII.card,
        backgroundColor: COLORS.limeSoft,
        opacity: reveal,
        transform: `translateY(${18 * (1 - reveal)}px) scaleY(${0.96 + reveal * 0.04})`,
        transformOrigin: "top",
        fontFamily: TYPOGRAPHY.fontFamily,
      }}
    >
      <div>
        <div
          style={{
            color: COLORS.optionSelectedText,
            fontSize: 14,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          推荐下一步
        </div>
        <div
          style={{
            marginTop: 8,
            color: COLORS.textPrimary,
            fontSize: 20,
            fontWeight: TYPOGRAPHY.weight.extraBold,
            lineHeight: 1.55,
          }}
        >
          {text}
        </div>
      </div>
      <div style={{display: "flex", gap: 12, flex: "0 0 auto"}}>
        <div
          style={{
            height: 48,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "0 17px",
            borderRadius: RADII.input,
            backgroundColor: COLORS.cta,
            color: COLORS.surface,
            fontSize: 15,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          <RotateCcw size={18} strokeWidth={2.3} />
          用推荐版本重新模拟
        </div>
        <div
          style={{
            height: 48,
            display: "inline-flex",
            alignItems: "center",
            gap: 8,
            padding: "0 17px",
            borderRadius: RADII.input,
            border: `1px solid ${COLORS.borderStrong}`,
            backgroundColor: COLORS.surface,
            color: COLORS.brand,
            fontSize: 15,
            fontWeight: TYPOGRAPHY.weight.extraBold,
          }}
        >
          查看完整分析
          <ArrowRight size={18} strokeWidth={2.3} />
        </div>
      </div>
    </section>
  );
};
