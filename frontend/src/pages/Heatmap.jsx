import { useState } from "react";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import WorldHeatmap from "@/components/WorldHeatmap";
import SegmentDistribution from "@/components/SegmentDistribution";
import { FAN_SEGMENTS, COUNTRIES } from "@/data/mock";

const EMOTION_COLOR = {
  joy: "#a3e635",
  anger: "#ef4444",
  surprise: "#3b82f6",
  fear: "#8b5cf6",
  disgust: "#84cc16",
  sadness: "#94a3b8",
  neutral: "#64748b",
};

export default function Heatmap() {
  const [activeSegment, setActiveSegment] = useState("all");
  const [hovered, setHovered] = useState(null);

  const totalVolume = COUNTRIES.reduce((a, c) => a + c.volume, 0);
  const avgSentiment = (
    COUNTRIES.reduce((a, c) => a + c.sentiment, 0) / COUNTRIES.length
  ).toFixed(2);

  return (
    <div data-testid="heatmap-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        {/* HEADER */}
        <Reveal>
          <div className="section-topline flex items-baseline justify-between flex-wrap gap-4">
            <div>
              <div className="overline">Global fan emotion</div>
              <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
                World <span className="gradient-lime">Heatmap</span>
                <span className="text-white/40"> / </span>
                <span className="gradient-ice">Segmentation</span>
              </h1>
            </div>
            <div className="flex items-center gap-4 text-[12px] text-white/60">
              <div className="flex items-center gap-2">
                <span className="w-1.5 h-1.5 bg-[#a3e635] pulse-dot rounded-full" />
                Sample · {totalVolume.toLocaleString()} msgs
              </div>
              <div>· Avg sentiment {avgSentiment}</div>
            </div>
          </div>
        </Reveal>

        {/* SEGMENT FILTERS */}
        <Reveal delay={0.1}>
          <div className="mt-10 flex flex-wrap gap-2" data-testid="heatmap-segment-filters">
            <button
              data-testid="segment-filter-all"
              onClick={() => setActiveSegment("all")}
              className={`text-[11px] font-semibold tracking-[0.16em] uppercase px-4 py-2 rounded-full border transition ${
                activeSegment === "all"
                  ? "border-white text-[#060a17] bg-white"
                  : "border-white/20 text-white/70 hover:text-white hover:border-white/40"
              }`}
            >
              All segments
            </button>
            {FAN_SEGMENTS.map((s) => {
              const active = activeSegment === s.id;
              return (
                <button
                  key={s.id}
                  data-testid={`heatmap-segment-${s.id}`}
                  onClick={() => setActiveSegment(s.id)}
                  className={`group inline-flex items-center gap-2 text-[11px] font-semibold tracking-[0.16em] uppercase px-4 py-2 rounded-full border transition`}
                  style={{
                    borderColor: active ? s.color : "rgba(255,255,255,0.15)",
                    background: active ? `${s.color}22` : "transparent",
                    color: active ? s.color : "rgba(255,255,255,0.7)",
                  }}
                >
                  <span className="w-2 h-2 rounded-full" style={{ background: s.color }} />
                  {s.name}
                </button>
              );
            })}
          </div>
        </Reveal>

        {/* WORLD MAP HEATMAP */}
        <Reveal delay={0.15}>
          <GlassCard className="mt-8 p-4 md:p-6 rounded-2xl overflow-hidden" hover={false}>
            <div className="flex items-baseline justify-between mb-4 px-2">
              <div className="overline">Country · Sentiment · Dominant emotion</div>
              <div className="text-[11px] text-white/50">poll · 2s</div>
            </div>

            <WorldHeatmap
              activeSegment={activeSegment}
              onHover={setHovered}
              hovered={hovered}
            />

            {/* Hover detail */}
            <div className="mt-4 border-t border-white/10 pt-4 min-h-[64px] px-2" data-testid="heatmap-hover-panel">
              {hovered ? (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                  <div><div className="overline">Country</div><div className="text-white text-lg font-semibold mt-1">{hovered.name}</div></div>
                  <div><div className="overline">Volume</div><div className="text-white text-lg font-semibold mt-1">{hovered.volume.toLocaleString()}</div></div>
                  <div><div className="overline">Sentiment</div><div className="text-white text-lg font-semibold mt-1">{hovered.sentiment.toFixed(2)}</div></div>
                  <div><div className="overline">Emotion</div><div className="text-lg font-semibold mt-1 capitalize" style={{ color: EMOTION_COLOR[hovered.emotion] }}>{hovered.emotion}</div></div>
                  <div><div className="overline">Segment</div><div className="text-white text-lg font-semibold mt-1 capitalize">{hovered.segment.replace("_", " ")}</div></div>
                </div>
              ) : (
                <div className="text-[12px] text-white/50">
                  Hover a heat blob for detail — blob size = volume, color = dominant segment, ring = signal strength.
                </div>
              )}
            </div>
          </GlassCard>
        </Reveal>

        {/* FIVE PERSONAS — with topline + distribution diagram */}
        <Reveal delay={0.2}>
          <div className="mt-16 section-topline flex items-baseline justify-between flex-wrap gap-4">
            <div>
              <div className="overline">Fan segmentation stats</div>
              <h2 className="display text-white text-3xl md:text-4xl mt-2">
                The <span className="gradient-fire">five personas</span>.
              </h2>
            </div>
            <div className="text-[11px] text-white/50">silhouette score · 0.62</div>
          </div>
        </Reveal>

        {/* Distribution diagram */}
        <Reveal delay={0.24}>
          <div className="mt-8">
            <SegmentDistribution />
          </div>
        </Reveal>

        {/* Persona cards */}
        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {FAN_SEGMENTS.map((s, i) => (
            <Reveal key={s.id} delay={0.05 * i}>
              <GlassCard
                className="p-5 h-full flex flex-col rounded-xl relative overflow-hidden"
                data-testid={`segment-card-${s.id}`}
              >
                {/* Top color bar */}
                <div
                  className="absolute top-0 left-0 right-0 h-1"
                  style={{ background: s.color }}
                />
                <div className="flex items-center justify-between pt-2">
                  <span
                    className="w-3 h-3 rounded-full"
                    style={{ background: s.color, boxShadow: `0 0 12px ${s.color}` }}
                  />
                  <div className="text-[11px] text-white/60 font-semibold">
                    {(s.share * 100).toFixed(0)}% share
                  </div>
                </div>
                <div className="display text-white text-xl mt-4 leading-tight">{s.name}</div>
                <div className="text-[11px] text-white/50 mt-1">{s.size.toLocaleString()} fans</div>

                <div className="mt-5 space-y-1.5">
                  {[
                    ["Engagement", s.engagement, "/100"],
                    ["Ann. value", `$${s.annual_value}`, ""],
                    ["Channel", s.channel, ""],
                    ["Churn", `${s.churn}%`, ""],
                  ].map(([k, v, u]) => (
                    <div key={k} className="flex justify-between text-[11px] border-b border-white/5 py-1.5">
                      <span className="text-white/50">{k}</span>
                      <span className="text-white font-semibold">{v}{u}</span>
                    </div>
                  ))}
                </div>

                <div className="mt-4">
                  <div className="overline">Traits</div>
                  <ul className="mt-2 space-y-1">
                    {s.traits.map((t) => (
                      <li key={t} className="text-[11px] text-white/70 flex gap-2">
                        <span style={{ color: s.color }}>›</span>{t}
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
