import {COLORS} from "../../design/tokens";

export type FlowParticleProps = {
  x: number;
  y: number;
  opacity?: number;
};

export const FlowParticle = ({x, y, opacity = 1}: FlowParticleProps) => {
  return (
    <circle
      cx={x}
      cy={y}
      r={7}
      fill={COLORS.lime}
      opacity={opacity}
      style={{filter: "drop-shadow(0 4px 8px rgba(79,157,122,0.28))"}}
    />
  );
};
