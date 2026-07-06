import { useMemo } from "react";
import { ComposableMap, Geographies, Geography } from "react-simple-maps";
import { motion } from "framer-motion";
import { COUNTRIES, FAN_SEGMENTS } from "@/data/mock";

const GEO_URL =
  "https://cdn.jsdelivr.net/npm/world-atlas@2/countries-110m.json";

// Simple equirectangular projection to place blob dots without depending on d3-geo internals of RSM
// (RSM projects <Geographies>; for our overlay we use its `projection` API via <ProjectionConfig>)
export default function WorldHeatmap({ activeSegment = "all", onHover, hovered }) {
  const maxVol = useMemo(
    () => Math.max(...COUNTRIES.map((c) => c.volume)),
    []
  );

  const projConfig = { scale: 155, center: [0, 20] };

  return (
    <div className="relative w-full" data-testid="world-heatmap">
      <ComposableMap
        projection="geoEqualEarth"
        projectionConfig={projConfig}
        width={980}
        height={480}
        style={{ width: "100%", height: "auto" }}
      >
        {/* Ocean glow */}
        <defs>
          <radialGradient id="ocean" cx="50%" cy="50%" r="70%">
            <stop offset="0%" stopColor="#0d1834" stopOpacity="1" />
            <stop offset="100%" stopColor="#060a17" stopOpacity="1" />
          </radialGradient>
          <linearGradient id="landStroke" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="rgba(255,255,255,0.14)" />
            <stop offset="100%" stopColor="rgba(255,255,255,0.05)" />
          </linearGradient>
        </defs>
        <rect x="0" y="0" width="980" height="480" fill="url(#ocean)" />

        <Geographies geography={GEO_URL}>
          {({ geographies, projection }) => (
            <>
              {geographies.map((geo) => (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  fill="rgba(148, 163, 184, 0.09)"
                  stroke="rgba(255,255,255,0.10)"
                  strokeWidth={0.5}
                  style={{
                    default: { outline: "none" },
                    hover: { outline: "none", fill: "rgba(148, 163, 184, 0.15)" },
                    pressed: { outline: "none" },
                  }}
                />
              ))}

              {/* Heat blobs at country coordinates */}
              {COUNTRIES.map((c) => {
                const seg = FAN_SEGMENTS.find((s) => s.id === c.segment);
                const [x, y] = projection(c.coords) || [null, null];
                if (x == null) return null;
                const dim = activeSegment !== "all" && c.segment !== activeSegment;
                const isHovered = hovered?.code === c.code;
                const baseR = 6 + (c.volume / maxVol) * 22;
                return (
                  <g
                    key={c.code}
                    data-testid={`heatmap-blob-${c.code}`}
                    transform={`translate(${x}, ${y})`}
                    onMouseEnter={() => onHover?.(c)}
                    onMouseLeave={() => onHover?.(null)}
                    style={{ cursor: "none", opacity: dim ? 0.15 : 1, transition: "opacity 0.4s" }}
                  >
                    {/* Outer halo */}
                    <motion.circle
                      r={baseR * 2.2}
                      fill={seg?.color || "#a3e635"}
                      opacity={0.16}
                      initial={{ scale: 0 }}
                      animate={{ scale: [1, 1.15, 1] }}
                      transition={{ duration: 3.2, repeat: Infinity, ease: "easeInOut" }}
                      style={{ transformOrigin: "center" }}
                    />
                    {/* Mid glow */}
                    <circle r={baseR * 1.3} fill={seg?.color || "#a3e635"} opacity={0.28} />
                    {/* Core */}
                    <circle
                      r={baseR * (isHovered ? 1.1 : 0.8)}
                      fill={seg?.color || "#a3e635"}
                      opacity={0.92}
                      style={{ transition: "r 0.2s" }}
                    />
                    {/* Ring */}
                    <circle
                      r={baseR * (isHovered ? 1.6 : 1.25)}
                      fill="none"
                      stroke={seg?.color || "#a3e635"}
                      strokeWidth={isHovered ? 1.5 : 0.8}
                      opacity={isHovered ? 0.9 : 0.55}
                    />
                    {(isHovered || c.volume > 120_000) && (
                      <text
                        y={-baseR - 6}
                        textAnchor="middle"
                        fill="#fff"
                        style={{
                          fontFamily: "'DM Sans', sans-serif",
                          fontSize: isHovered ? 11 : 9,
                          fontWeight: 700,
                          letterSpacing: "0.08em",
                        }}
                      >
                        {c.code}
                      </text>
                    )}
                  </g>
                );
              })}
            </>
          )}
        </Geographies>
      </ComposableMap>
    </div>
  );
}
