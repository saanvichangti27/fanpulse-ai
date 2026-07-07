import { useState } from "react";
import { Bell, Instagram, Youtube, Mail } from "lucide-react";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import WorldHeatmap from "@/components/WorldHeatmap";
import SegmentDistribution from "@/components/SegmentDistribution";
import MetricBars from "@/components/MetricBars";
import { FAN_SEGMENTS } from "@/data/mock";

const CHANNEL_ICON = { push: Bell, instagram: Instagram, youtube: Youtube, email: Mail };

export default function Heatmap() {
  const [activeSegment, setActiveSegment] = useState("all");
  const [hovered, setHovered] = useState(null);

  return (
    <div data-testid="heatmap-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        {/* HEADER */}
        <Reveal>
          <div className="section-topline">
            <div className="overline">Global fan emotion</div>
            <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
              World Heatmap / Segmentation
            </h1>
          </div>
        </Reveal>

        {/* FILTERS */}
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
                  className="inline-flex items-center gap-2 text-[11px] font-semibold tracking-[0.16em] uppercase px-4 py-2 rounded-full border transition"
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

        {/* MAP */}
        <Reveal delay={0.15}>
          <GlassCard className="mt-8 p-4 md:p-6 rounded-xl overflow-hidden" hover={false}>
            <WorldHeatmap activeSegment={activeSegment} onHover={setHovered} hovered={hovered} />

            <div className="mt-4 border-t border-white/10 pt-4 min-h-[64px] px-2" data-testid="heatmap-hover-panel">
              {hovered ? (
                <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
                  <div><div className="overline">Country</div><div className="text-white text-lg font-semibold mt-1">{hovered.name}</div></div>
                  <div><div className="overline">Volume</div><div className="text-white text-lg font-semibold mt-1">{hovered.volume.toLocaleString()}</div></div>
                  <div><div className="overline">Sentiment</div><div className="text-white text-lg font-semibold mt-1">{hovered.sentiment.toFixed(2)}</div></div>
                  <div><div className="overline">Emotion</div><div className="text-white text-lg font-semibold mt-1 capitalize">{hovered.emotion}</div></div>
                  <div><div className="overline">Segment</div><div className="text-white text-lg font-semibold mt-1 capitalize">{hovered.segment.replace("_", " ")}</div></div>
                </div>
              ) : (
                <div className="text-[12px] text-white/50">Hover a heat blob for country detail.</div>
              )}
            </div>
          </GlassCard>
        </Reveal>

        {/* PERSONAS SECTION */}
        <Reveal delay={0.2}>
          <div className="mt-20 section-topline">
            <div className="overline">Fan segmentation</div>
            <h2 className="display text-white text-3xl md:text-4xl mt-2">The five personas.</h2>
          </div>
        </Reveal>

        <Reveal delay={0.24}>
          <div className="mt-8 max-w-2xl">
            <SegmentDistribution />
          </div>
        </Reveal>

        <div className="mt-10 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {FAN_SEGMENTS.map((s, i) => {
            const Chan = CHANNEL_ICON[s.channel];
            return (
              <Reveal key={s.id} delay={0.05 * i}>
                <GlassCard
                  className="p-5 h-full flex flex-col rounded-xl relative overflow-hidden"
                  data-testid={`segment-card-${s.id}`}
                >
                  <div className="absolute top-0 left-0 right-0 h-1" style={{ background: s.color }} />
                  <div className="pt-2">
                    <span
                      className="w-9 h-9 rounded-lg flex items-center justify-center"
                      style={{ background: `${s.color}22`, border: `1px solid ${s.color}55` }}
                    >
                      {Chan && <Chan size={16} style={{ color: s.color }} />}
                    </span>
                  </div>
                  <div className="display text-white text-xl mt-4 leading-tight">{s.name}</div>
                  <div className="text-[11px] text-white/50 mt-1">{s.size.toLocaleString()} fans</div>

                  <div className="mt-4">
                    <MetricBars
                      engagement={s.engagement}
                      value={s.annual_value}
                      churn={s.churn}
                      color={s.color}
                    />
                  </div>

                  <div className="mt-4 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[12px]">
                    <div className="text-white/50">Ann. value</div>
                    <div className="text-white font-semibold text-right">${s.annual_value}</div>
                    <div className="text-white/50">Channel</div>
                    <div className="text-white font-semibold text-right capitalize">{s.channel}</div>
                  </div>

                  <div className="mt-4">
                    <div className="overline">Traits</div>
                    <ul className="mt-2 space-y-1">
                      {s.traits.slice(0, 2).map((t) => (
                        <li key={t} className="text-[12px] text-white/70 flex gap-2">
                          <span style={{ color: s.color }}>›</span>{t}
                        </li>
                      ))}
                    </ul>
                  </div>
                </GlassCard>
              </Reveal>
            );
          })}
        </div>
      </div>
    </div>
  );
}
