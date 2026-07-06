import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { FAN_SEGMENTS, COUNTRIES } from "@/data/mock";

const EMOTION_COLOR = {
  joy: "#F8FAFC",
  anger: "#EF4444",
  surprise: "#60A5FA",
  fear: "#A78BFA",
  disgust: "#84CC16",
  sadness: "#94A3B8",
  neutral: "#475569",
};

function sentimentBucket(s) {
  if (s >= 0.65) return { label: "hot", opacity: 1 };
  if (s >= 0.5) return { label: "warm", opacity: 0.75 };
  if (s >= 0.35) return { label: "cool", opacity: 0.5 };
  return { label: "cold", opacity: 0.28 };
}

export default function Heatmap() {
  const [activeSegment, setActiveSegment] = useState("all");
  const [hovered, setHovered] = useState(null);

  const filtered = useMemo(() => {
    return COUNTRIES.map((c) => ({
      ...c,
      dim: activeSegment !== "all" && c.segment !== activeSegment,
    }));
  }, [activeSegment]);

  const totalVolume = COUNTRIES.reduce((a, c) => a + c.volume, 0);
  const avgSentiment = (
    COUNTRIES.reduce((a, c) => a + c.sentiment, 0) / COUNTRIES.length
  ).toFixed(2);

  return (
    <div data-testid="heatmap-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        <Reveal>
          <div className="flex items-baseline justify-between flex-wrap gap-4">
            <div>
              <div className="overline">01 · Global Fan Emotion</div>
              <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
                World Heatmap <span className="metallic-text">/ Segmentation</span>
              </h1>
            </div>
            <div className="flex items-center gap-4 mono text-[11px] text-white/50">
              <div className="flex items-center gap-2"><span className="w-1.5 h-1.5 bg-white pulse-dot rounded-full" /> Sample · {totalVolume.toLocaleString()} msgs</div>
              <div>· Avg sentiment {avgSentiment}</div>
            </div>
          </div>
        </Reveal>

        {/* Filter chips */}
        <Reveal delay={0.1}>
          <div className="mt-10 flex flex-wrap gap-2" data-testid="heatmap-segment-filters">
            <button
              data-testid="segment-filter-all"
              onClick={() => setActiveSegment("all")}
              className={`mono text-[11px] tracking-[0.2em] uppercase px-4 py-2 border transition ${
                activeSegment === "all"
                  ? "border-white text-white bg-white/10"
                  : "border-white/15 text-white/60 hover:text-white hover:border-white/40"
              }`}
            >
              All segments
            </button>
            {FAN_SEGMENTS.map((s) => (
              <button
                key={s.id}
                data-testid={`heatmap-segment-${s.id}`}
                onClick={() => setActiveSegment(s.id)}
                className={`group inline-flex items-center gap-2 mono text-[11px] tracking-[0.2em] uppercase px-4 py-2 border transition ${
                  activeSegment === s.id
                    ? "border-white text-white bg-white/10"
                    : "border-white/15 text-white/60 hover:text-white hover:border-white/40"
                }`}
              >
                <span className="w-2 h-2" style={{ background: s.color }} />
                {s.name}
              </button>
            ))}
          </div>
        </Reveal>

        {/* Heatmap grid */}
        <Reveal delay={0.15}>
          <GlassCard className="mt-8 p-6 md:p-8" hover={false}>
            <div className="flex items-baseline justify-between mb-6">
              <div className="overline">Country · Sentiment · Dominant Emotion</div>
              <div className="mono text-[11px] text-white/40">poll · 2s</div>
            </div>

            <div className="grid grid-cols-4 sm:grid-cols-6 md:grid-cols-8 lg:grid-cols-11 gap-1.5">
              {filtered.map((c, i) => {
                const seg = FAN_SEGMENTS.find((s) => s.id === c.segment);
                const bucket = sentimentBucket(c.sentiment);
                const size = 0.7 + (c.volume / 220_000) * 0.6;
                return (
                  <motion.button
                    key={c.code}
                    data-testid={`heatmap-cell-${c.code}`}
                    onMouseEnter={() => setHovered(c)}
                    onMouseLeave={() => setHovered(null)}
                    initial={{ opacity: 0, scale: 0.8 }}
                    animate={{ opacity: c.dim ? 0.15 : 1, scale: 1 }}
                    transition={{ duration: 0.4, delay: i * 0.015 }}
                    className="group relative aspect-square hairline flex items-center justify-center overflow-hidden"
                    style={{
                      background: seg?.color,
                      opacity: c.dim ? 0.12 : bucket.opacity,
                    }}
                  >
                    <div
                      className="absolute inset-0"
                      style={{
                        background: `radial-gradient(circle at 30% 30%, rgba(255,255,255,0.35), transparent 60%)`,
                        transform: `scale(${size})`,
                      }}
                    />
                    <span className="relative mono text-[10px] font-bold text-[#050914]/80 group-hover:text-[#050914]">
                      {c.code}
                    </span>
                    <span
                      className="absolute bottom-0.5 right-0.5 w-1.5 h-1.5 rounded-full"
                      style={{ background: EMOTION_COLOR[c.emotion] }}
                      title={c.emotion}
                    />
                  </motion.button>
                );
              })}
            </div>

            {/* Hover detail */}
            <div className="mt-6 border-t border-white/10 pt-5 min-h-[64px]" data-testid="heatmap-hover-panel">
              {hovered ? (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                  <div><div className="overline">Country</div><div className="mono text-white text-lg mt-1">{hovered.name}</div></div>
                  <div><div className="overline">Volume</div><div className="mono text-white text-lg mt-1">{hovered.volume.toLocaleString()}</div></div>
                  <div><div className="overline">Sentiment</div><div className="mono text-white text-lg mt-1">{hovered.sentiment.toFixed(2)}</div></div>
                  <div><div className="overline">Emotion</div><div className="mono text-white text-lg mt-1 capitalize" style={{ color: EMOTION_COLOR[hovered.emotion] }}>{hovered.emotion}</div></div>
                  <div><div className="overline">Segment</div><div className="mono text-white text-lg mt-1 capitalize">{hovered.segment.replace("_", " ")}</div></div>
                </div>
              ) : (
                <div className="mono text-[12px] text-white/40">Hover a country cell for detail — cell tint = sentiment intensity, base color = dominant segment, dot = dominant emotion.</div>
              )}
            </div>
          </GlassCard>
        </Reveal>

        {/* SEGMENTATION STATS PANEL */}
        <Reveal delay={0.2}>
          <div className="mt-10">
            <div className="flex items-baseline justify-between">
              <div>
                <div className="overline">02 · Fan Segmentation Stats</div>
                <h2 className="display text-white text-3xl md:text-4xl mt-2">The five personas.</h2>
              </div>
              <div className="mono text-[11px] text-white/40">silhouette score · 0.62</div>
            </div>
          </div>
        </Reveal>

        <div className="mt-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {FAN_SEGMENTS.map((s, i) => (
            <Reveal key={s.id} delay={0.05 * i}>
              <GlassCard className="p-5 h-full flex flex-col" data-testid={`segment-card-${s.id}`}>
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5" style={{ background: s.color }} />
                  <div className="mono text-[11px] text-white/50">{(s.share * 100).toFixed(0)}% share</div>
                </div>
                <div className="display text-white text-xl mt-4 leading-tight">{s.name}</div>
                <div className="mono text-[11px] text-white/50 mt-1">{s.size.toLocaleString()} fans</div>

                <div className="mt-5 space-y-1.5">
                  {[
                    ["Engagement", s.engagement, "/100"],
                    ["Ann. value", `$${s.annual_value}`, ""],
                    ["Channel", s.channel, ""],
                    ["Churn", `${s.churn}%`, ""],
                  ].map(([k, v, u]) => (
                    <div key={k} className="flex justify-between mono text-[11px] border-b border-white/5 py-1">
                      <span className="text-white/50">{k}</span>
                      <span className="text-white">{v}{u}</span>
                    </div>
                  ))}
                </div>

                <div className="mt-4">
                  <div className="overline">Traits</div>
                  <ul className="mt-2 space-y-1">
                    {s.traits.map((t) => (
                      <li key={t} className="mono text-[11px] text-white/60 flex gap-2">
                        <span className="text-white/30">›</span>{t}
                      </li>
                    ))}
                  </ul>
                </div>
              </GlassCard>
            </Reveal>
          ))}
        </div>
      </div>
    </div>
  );
}
