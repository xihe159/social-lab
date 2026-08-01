import {interpolate, useCurrentFrame} from "remotion";

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

export type AnimatedNumberProps = {
  from: number;
  to: number;
  startFrame: number;
  durationInFrames: number;
  prefix?: string;
  suffix?: string;
  decimals?: number;
};

export const AnimatedNumber = ({
  from,
  to,
  startFrame,
  durationInFrames,
  prefix = "",
  suffix = "",
  decimals = 0,
}: AnimatedNumberProps) => {
  const frame = useCurrentFrame();
  const value = interpolate(
    frame,
    [startFrame, startFrame + durationInFrames],
    [from, to],
    CLAMP,
  );

  return (
    <>
      {prefix}
      {value.toFixed(decimals)}
      {suffix}
    </>
  );
};
