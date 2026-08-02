import { borderToken, type BorderToken } from "../tokenRefs";

interface DividerProps {
  tone?: BorderToken;
  orientation?: "horizontal" | "vertical";
}

/** Structural separator using the Border token group. */
export function Divider({ tone = "hairline", orientation = "horizontal" }: DividerProps) {
  const { color, width } = borderToken[tone];
  const isHorizontal = orientation === "horizontal";

  return (
    <div
      role="separator"
      aria-orientation={orientation}
      style={
        isHorizontal
          ? { borderTop: `${width} solid ${color}`, width: "100%", height: 0 }
          : { borderLeft: `${width} solid ${color}`, height: "100%", width: 0 }
      }
    />
  );
}
