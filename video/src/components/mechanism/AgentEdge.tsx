import {COLORS} from "../../design/tokens";

export type AgentEdgeProps = {
  x: number;
  y1: number;
  y2: number;
  progress: number;
};

export const AgentEdge = ({x, y1, y2, progress}: AgentEdgeProps) => {
  const safe = Math.max(0, Math.min(1, progress));
  const length = Math.abs(y2 - y1);

  return (
    <line
      x1={x}
      y1={y1}
      x2={x}
      y2={y2}
      stroke={COLORS.mechanismLine}
      strokeWidth={2}
      strokeLinecap="round"
      strokeDasharray={length}
      strokeDashoffset={length * (1 - safe)}
    />
  );
};
