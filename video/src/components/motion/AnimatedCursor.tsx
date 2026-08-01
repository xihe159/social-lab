import type {CSSProperties} from "react";
import {
  Easing,
  interpolate,
  useCurrentFrame,
} from "remotion";

import {COLORS} from "../../design/tokens";

export type CursorPoint = {
  frame: number;
  x: number;
  y: number;
};

export type CursorClickRange = {
  start: number;
  end: number;
};

export type AnimatedCursorProps = {
  points: readonly CursorPoint[];
  clicks?: readonly CursorClickRange[];
  visibleFrom?: number;
  visibleUntil?: number;
  size?: number;
  style?: CSSProperties;
};

const CLAMP = {
  extrapolateLeft: "clamp",
  extrapolateRight: "clamp",
} as const;

const getClickProgress = (
  frame: number,
  clicks: readonly CursorClickRange[],
): number => {
  let result = 0;

  for (const click of clicks) {
    if (frame < click.start || frame > click.end) {
      continue;
    }

    const middle = (click.start + click.end) / 2;

    const progress = interpolate(
      frame,
      [click.start, middle, click.end],
      [0, 1, 0],
      CLAMP,
    );

    result = Math.max(result, progress);
  }

  return result;
};

export const AnimatedCursor = ({
  points,
  clicks = [],
  visibleFrom = 0,
  visibleUntil = Number.POSITIVE_INFINITY,
  size = 42,
  style,
}: AnimatedCursorProps) => {
  const frame = useCurrentFrame();

  if (points.length < 2) {
    throw new Error(
      "AnimatedCursor requires at least two cursor points.",
    );
  }

  const inputRange = points.map((point) => point.frame);
  const xOutputRange = points.map((point) => point.x);
  const yOutputRange = points.map((point) => point.y);

  const x = interpolate(
    frame,
    inputRange,
    xOutputRange,
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  const y = interpolate(
    frame,
    inputRange,
    yOutputRange,
    {
      ...CLAMP,
      easing: Easing.bezier(0.16, 1, 0.3, 1),
    },
  );

  const entranceOpacity = interpolate(
    frame,
    [visibleFrom, visibleFrom + 8],
    [0, 1],
    CLAMP,
  );

  const exitOpacity = interpolate(
    frame,
    [visibleUntil - 8, visibleUntil],
    [1, 0],
    CLAMP,
  );

  const opacity = Math.min(
    entranceOpacity,
    exitOpacity,
  );

  const clickProgress = getClickProgress(
    frame,
    clicks,
  );

  const cursorScale = interpolate(
    clickProgress,
    [0, 1],
    [1, 0.86],
    CLAMP,
  );

  const ringScale = interpolate(
    clickProgress,
    [0, 1],
    [0.4, 1.7],
    CLAMP,
  );

  const ringOpacity = interpolate(
    clickProgress,
    [0, 0.35, 1],
    [0, 0.32, 0],
    CLAMP,
  );

  return (
    <div
      style={{
        position: "absolute",
        left: x,
        top: y,
        zIndex: 200,
        width: size,
        height: size,
        opacity,
        transform:
          `translate(-8px, -7px) scale(${cursorScale})`,
        transformOrigin: "8px 7px",
        pointerEvents: "none",
        willChange: "transform, opacity, left, top",
        ...style,
      }}
    >
      <div
        style={{
          position: "absolute",
          left: 5,
          top: 5,
          width: 24,
          height: 24,
          borderRadius: "50%",
          border: `2px solid ${COLORS.brand}`,
          opacity: ringOpacity,
          transform: `scale(${ringScale})`,
          transformOrigin: "center",
        }}
      />

      <svg
        width={size}
        height={size}
        viewBox="0 0 42 42"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        style={{
          overflow: "visible",
          filter:
            "drop-shadow(0 5px 7px rgba(35, 36, 58, 0.22))",
        }}
      >
        <path
          d="M7.3 4.8L30.2 24.3C31.5 25.4 30.7 27.5 29 27.5H19.1L14.7 36.7C14.1 38 12.2 37.9 11.7 36.6L4.7 7.1C4.3 5.5 6 3.8 7.3 4.8Z"
          fill="white"
          stroke={COLORS.textPrimary}
          strokeWidth="2.2"
          strokeLinejoin="round"
        />
      </svg>
    </div>
  );
};

