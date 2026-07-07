import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Clock, Copy, Check, ArrowRight } from "lucide-react";
import { toast } from "sonner";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { ChannelIcon, IndustryIcon, industryColor, channelColor } from "@/components/Icons";
import { STRATEGIES, INDUSTRIES, LOCATIONS, FAN_SEGMENTS } from "@/data/mock";

function Confidence({ value }) {
  const pct = Math.round(value * 100);
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 h-1 rounded-full bg-white/10 overflow-hidden">
        <div className="h-full rounded-full bg-white" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-[12px] text-white font-semibold tabular-nums">{pct}%</span>
    </div>
  );
}

function StrategyRow({ s, active, onClick }) {
  const seg = FAN_SEGMENTS.find((x) => x.id === s.segment);
  const ind = INDUSTRIES.find((x) => x.id === s.industry);
  return (
    <motion.button
      layout
      data-testid={`strategy-card-${s.id}`}
      onClick={onClick}
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className={`w-full text-left relative rounded-lg bg-white/[0.02] border p-5 transition ${
        active ? "border-white/40 bg-white/[0.05]" : "border-white/10 hover:border-white/25"
      }`}
    >
      {active && (
        <motion.span
          layoutId="active-strategy"
          className="absolute left-0 top-5 bottom-5 w-[3px] rounded-r bg-[#a3e635]"
        />
      )}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-3">
          <span
            className="w-8 h-8 rounded-md flex items-center justify-center"
            style={{ background: `${industryColor(s.industry)}18`, border: `1px solid ${industryColor(s.industry)}40` }}
          >
            <IndustryIcon id={s.industry} size={14} />
          </span>
          <div>
            <div className="text-[11px] text-white/60 uppercase tracking-widest">{ind?.label}</div>
            <div className="text-[11px] text-white/45 mt-0.5">{s.location}</div>
          </div>
        </div>
        <div className="text-[10px] text-white/70 flex items-center gap-1 border border-white/15 rounded-full px-2 py-1">
          <Clock className="w-3 h-3" />
          {s.ends_in_min}m
        </div>
      </div>

      <div className="display text-white text-lg mt-4 leading-snug">{s.copy.headline}</div>

      <div className="mt-5 pt-4 border-t border-white/5 flex items-center justify-between text-[12px]">
        <div className="flex items-center gap-4">
          <span className="inline-flex items-center gap-2 text-white/70">
            <span className="w-1.5 h-1.5 rounded-full" style={{ background: seg?.color }} />
            {seg?.name}
          </span>
          <span className="inline-flex items-center gap-1.5 text-white/70 capitalize">
            <ChannelIcon id={s.channel} size={12} />
            {s.channel}
          </span>
        </div>
        <div className="text-right">
          <div className="text-[10px] text-white/45 tracking-widest uppercase">ROAS</div>
          <div className="text-white font-bold text-base">×{s.roi.roas.toFixed(1)}</div>
        </div>
      </div>
    </motion.button>
  );
}

export default function Strategies() {
  const [location, setLocation] = useState("Global");
  const [industry, setIndustry] = useState("all");
  const [selectedId, setSelectedId] = useState(STRATEGIES[0].id);
  const [copied, setCopied] = useState(false);

  const filtered = useMemo(
    () =>
      STRATEGIES.filter((s) => {
        const locOk = location === "Global" || s.location === location || s.location === "Global";
        const indOk = industry === "all" || s.industry === industry;
        return locOk && indOk;
      }),
    [location, industry]
  );

  const selected = useMemo(
    () => filtered.find((s) => s.id === selectedId) || filtered[0],
    [filtered, selectedId]
  );

  const copyCopy = (text) => {
    navigator.clipboard?.writeText(text);
    setCopied(true);
    toast.success("Copy sent to clipboard");
    setTimeout(() => setCopied(false), 1400);
  };

  return (
    <div data-testid="strategies-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        {/* Header */}
        <Reveal>
          <div className="section-topline">
            <div className="overline">Recommendation engine</div>
            <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
              Marketing Strategies
            </h1>
          </div>
        </Reveal>

        {/* Filters */}
        <Reveal delay={0.08}>
          <div className="mt-10 border-b border-white/10 pb-6 flex flex-col md:flex-row md:items-end md:gap-8 gap-4" data-testid="strategy-filters">
            <div className="md:w-56">
              <div className="overline mb-2">Location</div>
              <select
                data-testid="filter-location"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full bg-transparent border-b border-white/20 text-white text-[14px] py-2 outline-none focus:border-[#a3e635]"
              >
                {LOCATIONS.map((l) => (
                  <option key={l} value={l} className="bg-[#0c1226]">{l}</option>
                ))}
              </select>
            </div>
            <div className="flex-1">
              <div className="overline mb-2">Marketing sector</div>
              <div className="flex flex-wrap gap-1.5">
                <button
                  data-testid="filter-industry-all"
                  onClick={() => setIndustry("all")}
                  className={`text-[11px] font-semibold tracking-tight px-3 py-1.5 rounded-full border transition ${
                    industry === "all"
                      ? "border-white text-[#060a17] bg-white"
                      : "border-white/15 text-white/70 hover:text-white hover:border-white/40"
                  }`}
                >
                  All
                </button>
                {INDUSTRIES.map((ind) => {
                  const active = industry === ind.id;
                  return (
                    <button
                      key={ind.id}
                      data-testid={`filter-industry-${ind.id}`}
                      onClick={() => setIndustry(ind.id)}
                      className="text-[11px] font-semibold tracking-tight px-3 py-1.5 rounded-full border transition flex items-center gap-1.5"
                      style={{
                        borderColor: active ? industryColor(ind.id) : "rgba(255,255,255,0.15)",
                        background: active ? `${industryColor(ind.id)}22` : "transparent",
                        color: active ? industryColor(ind.id) : "rgba(255,255,255,0.7)",
                      }}
                    >
                      <IndustryIcon id={ind.id} size={12} />
                      {ind.label}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        </Reveal>

        {/* List + Detail */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-4">
          <div className="lg:col-span-5 space-y-3" data-testid="strategy-list">
            <AnimatePresence initial={false}>
              {filtered.map((s) => (
                <StrategyRow
                  key={s.id}
                  s={s}
                  active={s.id === selected?.id}
                  onClick={() => setSelectedId(s.id)}
                />
              ))}
            </AnimatePresence>
            {filtered.length === 0 && (
              <div className="text-[12px] text-white/50 py-8 text-center border border-dashed border-white/10 rounded-lg">
                No strategies for this filter.
              </div>
            )}
          </div>

          <div className="lg:col-span-7">
            {selected && (
              <motion.div
                key={selected.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45 }}
              >
                <GlassCard className="p-8 rounded-xl" hover={false} data-testid="strategy-detail">
                  {/* Head */}
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-4">
                      <span
                        className="w-12 h-12 rounded-lg flex items-center justify-center"
                        style={{
                          background: `${industryColor(selected.industry)}18`,
                          border: `1px solid ${industryColor(selected.industry)}50`,
                        }}
                      >
                        <IndustryIcon id={selected.industry} size={22} />
                      </span>
                      <div>
                        <div className="overline">{INDUSTRIES.find((i) => i.id === selected.industry)?.label}</div>
                        <h2 className="display text-white text-3xl mt-1 leading-tight">
                          {selected.archetype}
                        </h2>
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="overline">ROAS</div>
                      <div className="display text-white text-4xl mt-1 tabular-nums">×{selected.roi.roas.toFixed(1)}</div>
                    </div>
                  </div>

                  {/* Meta rows */}
                  <div className="mt-8 grid grid-cols-4 gap-6 border-t border-b border-white/10 py-5">
                    <div>
                      <div className="overline">Segment</div>
                      <div className="text-white text-sm font-semibold mt-1.5">
                        {FAN_SEGMENTS.find((s) => s.id === selected.segment)?.name}
                      </div>
                    </div>
                    <div>
                      <div className="overline">Channel</div>
                      <div className="text-white text-sm font-semibold mt-1.5 flex items-center gap-1.5 capitalize">
                        <ChannelIcon id={selected.channel} size={13} />
                        {selected.channel}
                      </div>
                    </div>
                    <div>
                      <div className="overline">Location</div>
                      <div className="text-white text-sm font-semibold mt-1.5">{selected.location}</div>
                    </div>
                    <div>
                      <div className="overline">Expires in</div>
                      <div className="text-white text-sm font-semibold mt-1.5 flex items-center gap-1.5">
                        <Clock className="w-3.5 h-3.5" />
                        {selected.ends_in_min}m
                      </div>
                    </div>
                  </div>

                  {/* Copy */}
                  <div className="mt-6">
                    <div className="flex items-center justify-between mb-3">
                      <div className="overline">Marketing copy</div>
                      <button
                        data-testid="copy-variant"
                        onClick={() => copyCopy(`${selected.copy.headline}\n\n${selected.copy.body}`)}
                        className="text-[11px] font-semibold text-white/70 hover:text-white flex items-center gap-1"
                      >
                        {copied ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                        Copy
                      </button>
                    </div>
                    <div className="display text-white text-2xl leading-snug">{selected.copy.headline}</div>
                    <p className="text-[14px] text-white/70 mt-3 leading-relaxed">{selected.copy.body}</p>
                    <div className="mt-5 flex items-center gap-3 flex-wrap">
                      <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#052e16] px-4 py-2 rounded-full bg-gradient-to-r from-[#a3e635] to-[#22c55e]">
                        {selected.copy.cta} <ArrowRight className="w-3 h-3" />
                      </span>
                      {selected.copy.hashtags.map((h) => (
                        <span key={h} className="text-[12px] text-white/50">{h}</span>
                      ))}
                    </div>
                  </div>

                  {/* Why + Confidence */}
                  <div className="mt-8 grid grid-cols-1 md:grid-cols-3 gap-8 border-t border-white/10 pt-6">
                    <div className="md:col-span-2">
                      <div className="overline">Why this works</div>
                      <p className="text-[13px] text-white/70 mt-2 leading-relaxed">
                        {selected.trigger.desc}. Benchmarked against{" "}
                        <span className="text-white">{selected.benchmark}</span>.
                      </p>
                    </div>
                    <div>
                      <div className="overline">Confidence</div>
                      <div className="mt-3"><Confidence value={selected.confidence} /></div>
                      <div className="mt-3 text-[12px] text-white/50">
                        Est. revenue{" "}
                        <span className="text-white font-semibold">${selected.roi.revenue.toLocaleString()}</span>
                      </div>
                    </div>
                  </div>
                </GlassCard>
              </motion.div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
