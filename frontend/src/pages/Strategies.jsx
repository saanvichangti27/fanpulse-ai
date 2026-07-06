import { useMemo, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { AlertTriangle, Clock, Copy, Check, Sparkles } from "lucide-react";
import { toast } from "sonner";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { STRATEGIES, INDUSTRIES, LOCATIONS, FAN_SEGMENTS } from "@/data/mock";

const CHANNEL_ICON = {
  push: "◐",
  instagram: "◇",
  youtube: "▷",
  email: "✎",
};

function ConfidenceBar({ value }) {
  const pct = Math.round(value * 100);
  const tone = pct >= 75 ? "bg-white" : pct >= 60 ? "bg-white/60" : "bg-white/30";
  return (
    <div className="flex items-center gap-2">
      <div className="w-24 h-1 bg-white/10">
        <div className={`h-full ${tone}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="mono text-[11px] text-white">{pct}%</span>
    </div>
  );
}

export default function Strategies() {
  const [location, setLocation] = useState("Global");
  const [industry, setIndustry] = useState("all");
  const [selectedId, setSelectedId] = useState(STRATEGIES[0].id);
  const [copied, setCopied] = useState(null);

  const filtered = useMemo(() => {
    return STRATEGIES.filter((s) => {
      const locOk = location === "Global" || s.location === location || s.location === "Global";
      const indOk = industry === "all" || s.industry === industry;
      return locOk && indOk;
    });
  }, [location, industry]);

  const selected = useMemo(
    () => filtered.find((s) => s.id === selectedId) || filtered[0],
    [filtered, selectedId]
  );

  const copyCopy = (text, key) => {
    navigator.clipboard?.writeText(text);
    setCopied(key);
    toast.success("Copy blocked to clipboard");
    setTimeout(() => setCopied(null), 1400);
  };

  return (
    <div data-testid="strategies-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        <Reveal>
          <div className="flex items-baseline justify-between flex-wrap gap-3">
            <div>
              <div className="overline">02 · Recommendation Engine</div>
              <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
                Strategies <span className="metallic-text">/ Card Stream</span>
              </h1>
            </div>
            <div className="mono text-[11px] text-white/50">
              {filtered.length} card{filtered.length !== 1 && "s"} · auto & manual
            </div>
          </div>
        </Reveal>

        {/* FILTERS */}
        <Reveal delay={0.08}>
          <GlassCard className="mt-8 p-5" hover={false}>
            <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
              {/* Location */}
              <div className="md:col-span-3">
                <div className="overline">Location</div>
                <select
                  data-testid="filter-location"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  className="mt-2 w-full bg-transparent border-b border-white/20 focus:border-white/70 text-white mono text-[13px] py-2 outline-none appearance-none"
                >
                  {LOCATIONS.map((l) => (
                    <option key={l} value={l} className="bg-[#0a0f1f]">{l}</option>
                  ))}
                </select>
              </div>

              {/* Industry chips */}
              <div className="md:col-span-9">
                <div className="overline">Marketing sector</div>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  <button
                    data-testid="filter-industry-all"
                    onClick={() => setIndustry("all")}
                    className={`mono text-[10px] tracking-[0.18em] uppercase px-3 py-1.5 border transition ${
                      industry === "all"
                        ? "border-white text-white bg-white/10"
                        : "border-white/15 text-white/60 hover:text-white hover:border-white/40"
                    }`}
                  >
                    All
                  </button>
                  {INDUSTRIES.map((ind) => (
                    <button
                      key={ind.id}
                      data-testid={`filter-industry-${ind.id}`}
                      onClick={() => setIndustry(ind.id)}
                      className={`mono text-[10px] tracking-[0.18em] uppercase px-3 py-1.5 border transition flex items-center gap-2 ${
                        industry === ind.id
                          ? "border-white text-white bg-white/10"
                          : "border-white/15 text-white/60 hover:text-white hover:border-white/40"
                      }`}
                    >
                      {ind.primary && <span className="w-1 h-1 bg-white/80 rounded-full" />}
                      {ind.label}
                      {ind.compliance && <AlertTriangle className="w-3 h-3 text-yellow-300/80" />}
                    </button>
                  ))}
                </div>
              </div>
            </div>
          </GlassCard>
        </Reveal>

        {/* LIST + DETAIL */}
        <div className="mt-8 grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* LEFT: STRATEGIES LIST */}
          <div className="lg:col-span-5 space-y-3" data-testid="strategy-list">
            <AnimatePresence initial={false}>
              {filtered.map((s, i) => {
                const isActive = s.id === selected?.id;
                const seg = FAN_SEGMENTS.find((x) => x.id === s.segment);
                const ind = INDUSTRIES.find((x) => x.id === s.industry);
                return (
                  <motion.button
                    layout
                    key={s.id}
                    data-testid={`strategy-card-${s.id}`}
                    onClick={() => setSelectedId(s.id)}
                    initial={{ opacity: 0, y: 14 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: i * 0.03 }}
                    className={`w-full text-left relative bg-white/[0.03] backdrop-blur-xl border p-5 transition ${
                      isActive ? "border-white/50" : "border-white/10 hover:border-white/25"
                    }`}
                  >
                    {isActive && (
                      <motion.span layoutId="active-strategy" className="absolute -left-px top-4 bottom-4 w-[2px] bg-white" />
                    )}
                    <div className="flex items-start justify-between gap-3">
                      <div className="flex items-center gap-2">
                        <span className="overline">{ind?.label}</span>
                        {ind?.compliance && (
                          <span className="mono text-[9px] uppercase tracking-widest text-yellow-300/80 border border-yellow-300/30 px-1.5 py-0.5">
                            18+ · Restricted
                          </span>
                        )}
                      </div>
                      <div className="mono text-[10px] text-white/50 flex items-center gap-1.5">
                        <Clock className="w-3 h-3" />
                        {s.ends_in_min}m
                      </div>
                    </div>

                    <div className="display text-white text-lg mt-3 leading-snug">
                      {s.copy.headline}
                    </div>

                    <div className="mt-4 flex flex-wrap items-center gap-3 mono text-[11px] text-white/60">
                      <span className="inline-flex items-center gap-1.5">
                        <span className="w-1.5 h-1.5" style={{ background: seg?.color }} />
                        {seg?.name}
                      </span>
                      <span>·</span>
                      <span className="uppercase">{CHANNEL_ICON[s.channel]} {s.channel}</span>
                      <span>·</span>
                      <span>{s.location}</span>
                      <span className="ml-auto text-white">×{s.multipliers.total.toFixed(2)}</span>
                    </div>
                  </motion.button>
                );
              })}
            </AnimatePresence>
            {filtered.length === 0 && (
              <div className="mono text-[12px] text-white/40 py-8 text-center border border-dashed border-white/10">
                Not enough live signal for this filter yet.
              </div>
            )}
          </div>

          {/* RIGHT: DETAIL */}
          <div className="lg:col-span-7">
            {selected && (
              <motion.div
                key={selected.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.45 }}
              >
                <GlassCard className="p-6 md:p-8" hover={false} data-testid="strategy-detail">
                  {/* Head */}
                  <div className="flex items-start justify-between gap-3 flex-wrap">
                    <div>
                      <div className="overline">
                        {INDUSTRIES.find((i) => i.id === selected.industry)?.label} · {selected.location}
                      </div>
                      <h2 className="display text-white text-3xl md:text-4xl mt-2 leading-tight">
                        {selected.archetype}
                      </h2>
                    </div>
                    <div className="text-right">
                      <div className="overline">Multiplier</div>
                      <div className="display metallic-text text-5xl mt-1">×{selected.multipliers.total.toFixed(2)}</div>
                    </div>
                  </div>

                  {selected.compliance_note && (
                    <div className="mt-4 mono text-[11px] flex items-start gap-2 text-yellow-200/80 border border-yellow-300/25 bg-yellow-300/5 p-3">
                      <AlertTriangle className="w-3.5 h-3.5 mt-0.5" />
                      {selected.compliance_note}
                    </div>
                  )}

                  {/* Trigger */}
                  <div className="mt-6 grid grid-cols-3 gap-4 border-t border-white/10 pt-5">
                    <div>
                      <div className="overline">Trigger</div>
                      <div className="mono text-white text-sm mt-1 capitalize">{selected.trigger.type}</div>
                      <div className="mono text-[10px] text-white/50 mt-1">{selected.trigger.moment_id}</div>
                    </div>
                    <div>
                      <div className="overline">Window</div>
                      <div className="mono text-white text-sm mt-1">{selected.window_min}m</div>
                      <div className="mono text-[10px] text-white/50 mt-1">expires in {selected.ends_in_min}m</div>
                    </div>
                    <div>
                      <div className="overline">Source</div>
                      <div className="mono text-white text-sm mt-1 flex items-center gap-1.5">
                        {selected.ai_generated ? <><Sparkles className="w-3 h-3" /> AI</> : "Fallback"}
                      </div>
                      <div className="mono text-[10px] text-white/50 mt-1">
                        conf · <ConfidenceBar value={selected.confidence} />
                      </div>
                    </div>
                  </div>

                  {/* COPY A + B */}
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
                    {[["A", selected.copy], ["B", selected.variant_b]].map(([label, copy]) => (
                      <div key={label} className="border border-white/10 p-4 relative">
                        <div className="flex items-center justify-between">
                          <div className="overline">Variant {label}</div>
                          <button
                            data-testid={`copy-variant-${label.toLowerCase()}`}
                            onClick={() => copyCopy(`${copy.headline}\n\n${copy.body}\n\n${copy.cta}`, `${selected.id}-${label}`)}
                            className="mono text-[10px] tracking-widest uppercase text-white/60 hover:text-white flex items-center gap-1"
                          >
                            {copied === `${selected.id}-${label}` ? <Check className="w-3 h-3" /> : <Copy className="w-3 h-3" />}
                            Copy
                          </button>
                        </div>
                        <div className="display text-white text-lg mt-2 leading-snug">{copy.headline}</div>
                        <p className="mono text-[12px] text-white/60 mt-2 leading-relaxed">{copy.body}</p>
                        <div className="mt-3 flex flex-wrap items-center gap-2">
                          <span className="mono text-[10px] tracking-widest uppercase border border-white/20 px-2 py-1">{copy.cta}</span>
                          {copy.hashtags.map((h) => (
                            <span key={h} className="mono text-[10px] text-white/50">{h}</span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>

                  {/* REASON & ROI */}
                  <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div className="border border-white/10 p-4">
                      <div className="overline mb-3">Reason · Multiplier breakdown</div>
                      {Object.entries(selected.multipliers).filter(([k]) => k !== "total").map(([k, v]) => (
                        <div key={k} className="flex items-center gap-3 mb-2">
                          <span className="mono text-[11px] text-white/50 w-28 capitalize">{k.replace("_", " ")}</span>
                          <div className="flex-1 h-1 bg-white/10">
                            <div className="h-full bg-white" style={{ width: `${Math.min(100, (v / 2) * 100)}%` }} />
                          </div>
                          <span className="mono text-[11px] text-white">×{v.toFixed(2)}</span>
                        </div>
                      ))}
                      <div className="mt-3 mono text-[11px] text-white/50 border-t border-white/5 pt-3">
                        Evidence — {selected.trigger.desc}. Benchmark: <span className="text-white/80">{selected.benchmark}</span>
                      </div>
                    </div>

                    <div className="border border-white/10 p-4">
                      <div className="overline mb-3">ROI projection · funnel</div>
                      <div className="space-y-2">
                        {[
                          ["Impressions", selected.roi.impressions],
                          ["Reach", selected.roi.reach],
                          ["Clicks", selected.roi.clicks],
                          ["Conversions", selected.roi.conv],
                          ["Revenue $", selected.roi.revenue],
                        ].map(([k, v]) => (
                          <div key={k} className="flex justify-between mono text-[11px] border-b border-white/5 pb-1.5">
                            <span className="text-white/50">{k}</span>
                            <span className="text-white">{v.toLocaleString()}</span>
                          </div>
                        ))}
                      </div>
                      <div className="mt-4 flex items-baseline justify-between">
                        <span className="overline">ROAS</span>
                        <span className="display metallic-text text-3xl">×{selected.roi.roas.toFixed(1)}</span>
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
