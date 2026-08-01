import type {ReactNode} from "react";

import {COLORS, RADII} from "../../design/tokens";

export type EvidenceHighlightProps = {
  children: ReactNode;
  progress: number;
};

export const EvidenceHighlight = ({
  children,
  progress,
}: EvidenceHighlightProps) => {
  const safe = Math.max(0, Math.min(1, progress));

  return (
    <span
      style={{
        position: "relative",
        display: "inline",
        padding: "2px 4px",
        margin: "0 -4px",
        borderRadius: RADII.input,
        background:
          `linear-gradient(90deg, ${COLORS.limeSoft} 0%, ` +
          `${COLORS.limeSoft} ${safe * 100}%, transparent ${safe * 100}%)`,
        boxDecorationBreak: "clone",
        WebkitBoxDecorationBreak: "clone",
      }}
    >
      {children}
    </span>
  );
};
