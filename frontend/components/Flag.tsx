import type { CSSProperties } from "react";

export default function Flag({
  src,
  code,
  style,
}: {
  src?: string;
  code?: string;
  style?: CSSProperties;
}) {
  if (!src) {
    return (
      <span
        className="flag"
        style={{
          display: "inline-grid",
          placeItems: "center",
          fontSize: 10,
          color: "#8a95b2",
          ...style,
        }}
      >
        {code || "?"}
      </span>
    );
  }
  // eslint-disable-next-line @next/next/no-img-element
  return <img className="flag" src={src} alt={code || ""} style={style} />;
}
