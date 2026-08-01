import type {CSSProperties, ReactNode} from "react";
import {
  COLORS,
  LAYOUT,
  RADII,
  SHADOWS,
  TYPOGRAPHY,
} from "../design/tokens";

export type BrowserWindowProps = {
  children: ReactNode;

  /**
   * 是否显示非常轻量的演示窗口顶部栏。
   * Social Lab 正式产品镜头大多数情况下应保持 false。
   */
  showChrome?: boolean;

  title?: string;
  width?: number | string;
  height?: number | string;

  style?: CSSProperties;
  contentStyle?: CSSProperties;
};

const ChromeDot = () => {
  return (
    <div
      style={{
        width: 10,
        height: 10,
        borderRadius: "50%",
        backgroundColor: COLORS.borderStrong,
      }}
    />
  );
};

export const BrowserWindow = ({
  children,
  showChrome = false,
  title = "Social Lab",
  width = "100%",
  height = "auto",
  style,
  contentStyle,
}: BrowserWindowProps) => {
  return (
    <div
      style={{
        width,
        height,
        boxSizing: "border-box",
        overflow: "hidden",
        borderRadius: RADII.card,
        border: `1px solid ${COLORS.border}`,
        backgroundColor: COLORS.surface,
        boxShadow: SHADOWS.card,
        ...style,
      }}
    >
      {showChrome ? (
        <div
          style={{
            height: LAYOUT.browserChromeHeight,
            boxSizing: "border-box",
            display: "grid",
            gridTemplateColumns: "1fr auto 1fr",
            alignItems: "center",
            padding: "0 18px",
            borderBottom: `1px solid ${COLORS.border}`,
            backgroundColor: COLORS.pageSoft,
          }}
        >
          <div
            style={{
              display: "flex",
              gap: 7,
              alignItems: "center",
            }}
          >
            <ChromeDot />
            <ChromeDot />
            <ChromeDot />
          </div>

          <div
            style={{
              color: COLORS.textSecondary,
              fontFamily: TYPOGRAPHY.fontFamily,
              fontSize: 15,
              fontWeight: TYPOGRAPHY.weight.medium,
              whiteSpace: "nowrap",
            }}
          >
            {title}
          </div>

          <div />
        </div>
      ) : null}

      <div
        style={{
          minWidth: 0,
          minHeight: 0,
          boxSizing: "border-box",
          ...contentStyle,
        }}
      >
        {children}
      </div>
    </div>
  );
};
