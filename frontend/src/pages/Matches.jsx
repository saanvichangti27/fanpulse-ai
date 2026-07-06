import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { TrendingUp } from "lucide-react";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import Flag from "@/components/Flag";
import { MomentIcon, momentColor } from "@/components/Icons";
import { MATCHES, SENTIMENT_TIMELINE, MOMENTS } from "@/data/mock";

const STATUS_META = {
  live:     { label: "LIVE",     color: "#a3e635", dotClass: "bg-[#a3e635] pulse-dot" },
  upcoming: { label: "UPCOMING", color: "#38bdf8", dotClass: "bg-[#38bdf8]" },
  finished: { label: "FT",       color: "#94a3b8", dotClass: "bg-white/30" },
};

function Gauge({ value }) {
  const pct = Math.max(0, Math.min(100, value));
  const r = 58;
  const c = 2 * Math.PI * r;
  const off = c * (1 - pct / 100);
  return (
    <div className="relative w-[150px] h-[150px]" data-testid="demand-gauge">
      <svg viewBox="0 0 150 150" className="w-full h-full -rotate-90">
        <defs>
          <linearGradient id="gauge-grad" x1="0" y1="0" x2="1" y2="1">
            <stop offset="0%" stopColor="#a3e635" />
            <stop offset="60%" stopColor="#22c55e" />
            <stop offset="100%" stopColor="#3b82f6" />
          </linearGradient>
        </defs>
        <circle cx="75" cy="75" r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="7" fill="none" />
        <motion.circle
          cx="75" cy="75" r={r}
          stroke="url(#gauge-grad)" strokeWidth="7" fill="none" strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: off }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="display gradient-lime text-4xl">{pct}</div>
        <div className="overline mt-1">Demand</div>
      </div>
    </div>
  );
}

function ScheduleItem({ m, active, onClick }) {
  const st = STATUS_META[m.status];
  const dateStr = new Date(m.kickoff).toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  return (
    <button
      data-testid={`match-item-${m.id}`}
      onClick={onClick}
      className={`w-full text-left p-3 rounded-xl border transition ${
        active ? "border-[#a3e635]/60 bg-[#a3e635]/[0.05]" : "border-white/10 hover:border-white/25"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="text-[10px] tracking-wider text-white/50">{m.tournament_stage}</div>
        <div className="flex items-center gap-1.5" style={{ color: st.color }}>
          <span className={`w-1.5 h-1.5 rounded-full ${st.dotClass}`} />
          <span className="text-[10px] font-bold tracking-widest">{st.label}</span>
        </div>
      </div>
      <div className="mt-2 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Flag iso2={m.home_iso2} size={20} />
          <span className="display text-white text-sm">{m.home_short}</span>
          <span className="text-white/40 text-[11px]">vs</span>
          <span className="display text-white text-sm">{m.away_short}</span>
          <Flag iso2={m.away_iso2} size={20} />
        </div>
        {m.status !== "upcoming" && (
          <div className="text-white text-sm font-bold">
            {m.score.home}–{m.score.away}
            {m.status === "live" && <span className="text-white/50 text-[10px] ml-1">{m.score.minute}'</span>}
          </div>
        )}
      </div>
      <div className="mt-2 flex items-center justify-between text-[10px] text-white/45">
        <span>{dateStr} · {m.venue.city}</span>
        <span className="text-white/70">DI {m.demand_index}</span>
      </div>
    </button>
  );
}

export default function Matches() {
  const [selectedId, setSelectedId] = useState(MATCHES[0].id);
  const selected = useMemo(() => MATCHES.find((m) => m.id === selectedId), [selectedId]);
  const topMoments = MOMENTS.filter((mo) => mo.type !== "kickoff").slice(0, 4);

  return (
    <div data-testid="matches-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        <Reveal>
          <div className="section-topline flex items-baseline justify-between flex-wrap gap-4">
            <div>
              <div className="overline">Match console</div>
              <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
                Matches <span className="gradient-fire">/ Demand</span>
              </h1>
            </div>
            <div className="text-[12px] text-white/60">Live · Upcoming · History</div>
          </div>
        </Reveal>

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* SCHEDULE */}
          <aside className="lg:col-span-4">
            <GlassCard className="p-4 rounded-2xl" hover={false} data-testid="match-schedule">
              <div className="flex items-baseline justify-between px-1 pb-3 border-b border-white/10">
                <div className="overline">Schedule</div>
                <div className="text-[10px] text-white/50">{MATCHES.length} fixtures</div>
              </div>
              <div className="mt-3 space-y-2">
                {MATCHES.map((m) => (
                  <ScheduleItem
                    key={m.id}
                    m={m}
                    active={m.id === selected.id}
                    onClick={() => setSelectedId(m.id)}
                  />
                ))}
              </div>
            </GlassCard>
          </aside>

          {/* MAIN */}
          <div className="lg:col-span-8 space-y-4">
            {/* HEAD */}
            <GlassCard className="p-6 md:p-8 rounded-2xl overflow-hidden relative" hover={false} data-testid="match-detail-head">
              {/* accent gradient */}
              <div
                aria-hidden
                className="absolute -top-24 -right-24 w-72 h-72 rounded-full opacity-40 blur-3xl"
                style={{ background: "radial-gradient(circle, rgba(163,230,53,0.35), transparent 65%)" }}
              />
              <div className="relative">
                <div className="overline">{selected.tournament_stage} · {selected.venue.city}</div>
                <div className="mt-3 flex items-center gap-4 flex-wrap">
                  <div className="flex items-center gap-3">
                    <Flag iso2={selected.home_iso2} size={40} />
                    <span className="display text-white text-3xl md:text-4xl">{selected.home}</span>
                  </div>
                  <span className="text-white/40 text-sm">vs</span>
                  <div className="flex items-center gap-3">
                    <span className="display text-white text-3xl md:text-4xl">{selected.away}</span>
                    <Flag iso2={selected.away_iso2} size={40} />
                  </div>
                </div>

                <div className="mt-6 flex items-center justify-between flex-wrap gap-6">
                  <Gauge value={selected.demand_index} />
                  <div className="flex gap-3">
                    <div className="rounded-xl border border-white/10 px-4 py-3 min-w-[130px]">
                      <div className="overline">Sellout</div>
                      <div className="display gradient-ice text-2xl mt-1">
                        {Math.round(selected.sellout_prob * 100)}%
                      </div>
                    </div>
                    <div className="rounded-xl border border-white/10 px-4 py-3 min-w-[130px]">
                      <div className="overline">Excitement</div>
                      <div className="display gradient-fire text-2xl mt-1">
                        {selected.excitement}<span className="text-white/40 text-sm">/100</span>
                      </div>
                    </div>
                    <div className="rounded-xl border border-white/10 px-4 py-3 min-w-[130px]">
                      <div className="overline">Δ Forecast</div>
                      <div className="display text-white text-2xl mt-1 flex items-center gap-1">
                        <TrendingUp className="w-4 h-4 text-[#a3e635]" />
                        {selected.demand_index - selected.baseline_forecast >= 0 ? "+" : ""}
                        {selected.demand_index - selected.baseline_forecast}
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </GlassCard>

            {/* TIMELINE */}
            <GlassCard className="p-6 rounded-2xl" hover={false} data-testid="sentiment-timeline">
              <div className="flex items-baseline justify-between mb-3">
                <div className="overline">Sentiment timeline</div>
                <div className="text-[10px] text-white/50">5-min buckets</div>
              </div>
              <div className="w-full h-[200px]">
                <ResponsiveContainer>
                  <AreaChart data={SENTIMENT_TIMELINE} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g-pos" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#a3e635" stopOpacity={0.8} />
                        <stop offset="100%" stopColor="#a3e635" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="minute" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(6,10,23,0.92)",
                        border: "1px solid rgba(163,230,53,0.35)",
                        borderRadius: 8, color: "#fff", fontSize: 12,
                      }}
                    />
                    <Area type="monotone" dataKey="positive" stroke="#a3e635" strokeWidth={2} fill="url(#g-pos)" />
                    <Area type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={1.4} fillOpacity={0} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 flex items-center gap-4 text-[11px] text-white/60">
                <span className="inline-flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#a3e635]" /> Positive</span>
                <span className="inline-flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#ef4444]" /> Negative</span>
              </div>
            </GlassCard>

            {/* KEY MOMENTS */}
            <GlassCard className="p-6 rounded-2xl" hover={false} data-testid="moments-list">
              <div className="flex items-baseline justify-between mb-3">
                <div className="overline">Key moments</div>
                <div className="text-[10px] text-white/50">{topMoments.length} events</div>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                {topMoments.map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center gap-3 rounded-lg border border-white/10 p-3"
                    style={{ background: `linear-gradient(90deg, ${momentColor(m.type)}10, transparent 60%)` }}
                  >
                    <span
                      className="w-9 h-9 rounded-lg flex items-center justify-center"
                      style={{ background: `${momentColor(m.type)}22`, border: `1px solid ${momentColor(m.type)}55` }}
                    >
                      <MomentIcon type={m.type} size={16} />
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-[13px] text-white font-semibold capitalize truncate">{m.type}</div>
                      <div className="text-[11px] text-white/60 truncate">{m.desc}</div>
                    </div>
                    <div className="text-[11px] font-bold text-white/80 shrink-0">{m.minute}'</div>
                  </div>
                ))}
              </div>
            </GlassCard>
          </div>
        </div>
      </div>
    </div>
  );
}
