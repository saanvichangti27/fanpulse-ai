import { useState } from "react";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import WorldHeatmap from "@/components/WorldHeatmap";
import SegmentDistribution from "@/components/SegmentDistribution";
import PersonaRadar from "@/components/PersonaRadar";
import { FAN_SEGMENTS } from "@/data/mock";

export default function Heatmap() {
  const [activeSegment, setActiveSegment] = useState("all");
  const [hovered, setHovered] = useState(null);

  return (
    <div data-testid="heatmap-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        <Reveal>
          <div >

            <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
              Global Fan Emotions
            </h1>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <div className="mt-10 flex flex-wrap gap-2" data-testid="heatmap-segment-filters">
            <button
              data-testid="segment-filter-all"
              onClick={() => setActiveSegment("all")}
              className={`text-[11px] font-semibold tracking-[0.16em] uppercase px-4 py-2 rounded-full border transition ${activeSegment === "all"
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
        <br></br>
        <br></br>
        <br></br>

        <Reveal delay={0.2}>
          <div>

            <h2 className="display text-white text-3xl md:text-4xl mt-2">Fan Segmentation</h2>
          </div>
        </Reveal>

        {/* Full-width distribution bar */}
        <Reveal delay={0.24}>
          <div className="mt-8 w-full">
            <SegmentDistribution />
          </div>
        </Reveal>

        {/* Persona cards */}
        <div className="mt-12 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-3">
          {FAN_SEGMENTS.map((s, i) => (
            <Reveal key={s.id} delay={0.05 * i}>
              <GlassCard
                className="p-5 h-full flex flex-col rounded-xl relative overflow-hidden"
                data-testid={`segment-card-${s.id}`}
              >
                <div className="absolute top-0 left-0 right-0 h-1" style={{ background: s.color }} />

                <div className="pt-2 flex items-start justify-between">
                  <div className="display text-white text-2xl mt-2 leading-tight">{s.name}</div>
                  <div className="display text-[#a3e635] text-xl mt-2 tabular-nums whitespace-nowrap">
                    {(s.share * 100).toFixed(1)}%
                  </div>
                </div>

                {/* Radar graph */}
                <div className="mt-3">
                  <PersonaRadar segment={s} color={s.color} />
                </div>

                <div className="mt-3 grid grid-cols-2 gap-x-3 gap-y-1.5 text-[12px] border-t border-white/5 pt-3">
                  <div className="text-white/50">Fans</div>
                  <div className="text-white font-semibold text-right tabular-nums">{s.size.toLocaleString()}</div>
                  <div className="text-white/50">Ann. value</div>
                  <div className="text-white font-semibold text-right">${s.annual_value}</div>
                  <div className="text-white/50">Channel</div>
                  <div className="text-white font-semibold text-right capitalize">{s.channel}</div>
                </div>
              </GlassCard>
            </Reveal>
          ))}
        </div>
      </div>
    </div>
  );
}
