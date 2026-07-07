import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
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
        <circle cx="75" cy="75" r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="6" fill="none" />
        <motion.circle
          cx="75" cy="75" r={r}
          stroke="#a3e635" strokeWidth="6" fill="none" strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: off }}
          transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="display text-white text-4xl tabular-nums">{pct}</div>
        <div className="overline mt-1">Demand</div>
      </div>
    </div>
  );
}

function StatCard({ label, value }) {
  return (
    <div className="border-l border-white/10 pl-5">
      <div className="overline">{label}</div>
      <div className="display text-white text-2xl mt-2 tabular-nums">{value}</div>
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
      className={`w-full text-left p-4 rounded-lg border transition ${
        active ? "border-white/40 bg-white/[0.04]" : "border-white/10 hover:border-white/25"
      }`}
    >
      <div className="flex items-center justify-between">
        <div className="text-[10px] tracking-widest text-white/45 uppercase">{m.tournament_stage}</div>
        <div className="flex items-center gap-1.5" style={{ color: st.color }}>
          <span className={`w-1.5 h-1.5 rounded-full ${st.dotClass}`} />
          <span className="text-[10px] font-bold tracking-widest">{st.label}</span>
        </div>
      </div>
      <div className="mt-3 flex items-center justify-between">
        <div className="flex items-center gap-2.5">
          <Flag iso2={m.home_iso2} size={22} />
          <span className="display text-white text-[15px]">{m.home_short}</span>
          <span className="text-white/40 text-[11px]">vs</span>
          <span className="display text-white text-[15px]">{m.away_short}</span>
          <Flag iso2={m.away_iso2} size={22} />
        </div>
        {m.status !== "upcoming" && (
          <div className="text-white text-sm font-bold tabular-nums">
            {m.score.home}–{m.score.away}
            {m.status === "live" && <span className="text-white/50 text-[10px] ml-1">{m.score.minute}'</span>}
          </div>
        )}
      </div>
      <div className="mt-3 flex items-center justify-between text-[11px] text-white/50">
        <span>{dateStr} · {m.venue.city}</span>
      </div>
    </button>
  );
}

export default function Matches() {
  const [selectedId, setSelectedId] = useState(MATCHES[0].id);
  const selected = useMemo(() => MATCHES.find((m) => m.id === selectedId), [selectedId]);
  const topMoments = MOMENTS.filter((mo) => mo.type !== "kickoff").slice(0, 4);
  const delta = selected.demand_index - selected.baseline_forecast;

  return (
    <div data-testid="matches-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        <Reveal>
          <div className="section-topline">
            <div className="overline">Match console</div>
            <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
              Matches / Demand
            </h1>
          </div>
        </Reveal>

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-6">
          {/* SCHEDULE */}
          <aside className="lg:col-span-4">
            <div className="pb-3 border-b border-white/10 mb-4">
              <div className="overline">Schedule</div>
            </div>
            <div className="space-y-3" data-testid="match-schedule">
              {MATCHES.map((m) => (
                <ScheduleItem
                  key={m.id}
                  m={m}
                  active={m.id === selected.id}
                  onClick={() => setSelectedId(m.id)}
                />
              ))}
            </div>
          </aside>

          {/* MAIN */}
          <div className="lg:col-span-8 space-y-6">
            {/* HEAD */}
            <div className="border-b border-white/10 pb-8" data-testid="match-detail-head">
              <div className="overline">{selected.tournament_stage} · {selected.venue.city}</div>
              <div className="mt-4 flex items-center gap-5 flex-wrap">
                <div className="flex items-center gap-3">
                  <Flag iso2={selected.home_iso2} size={44} />
                  <span className="display text-white text-4xl md:text-5xl">{selected.home}</span>
                </div>
                <span className="text-white/40 text-sm">vs</span>
                <div className="flex items-center gap-3">
                  <span className="display text-white text-4xl md:text-5xl">{selected.away}</span>
                  <Flag iso2={selected.away_iso2} size={44} />
                </div>
              </div>

              <div className="mt-8 flex items-center gap-8 flex-wrap">
                <Gauge value={selected.demand_index} />
                <div className="flex gap-8">
                  <StatCard label="Sellout" value={`${Math.round(selected.sellout_prob * 100)}%`} />
                  <StatCard label="Excitement" value={selected.excitement} />
                  <StatCard label="Δ Forecast" value={`${delta >= 0 ? "+" : ""}${delta}`} />
                </div>
              </div>
            </div>

            {/* TIMELINE */}
            <GlassCard className="p-6 rounded-xl" hover={false} data-testid="sentiment-timeline">
              <div className="overline mb-4">Sentiment timeline</div>
              <div className="w-full h-[200px]">
                <ResponsiveContainer>
                  <AreaChart data={SENTIMENT_TIMELINE} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g-pos" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#a3e635" stopOpacity={0.55} />
                        <stop offset="100%" stopColor="#a3e635" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="minute" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10 }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(6,10,23,0.94)",
                        border: "1px solid rgba(255,255,255,0.15)",
                        borderRadius: 6, color: "#fff", fontSize: 12,
                      }}
                    />
                    <Area type="monotone" dataKey="positive" stroke="#a3e635" strokeWidth={2} fill="url(#g-pos)" />
                    <Area type="monotone" dataKey="negative" stroke="#ef4444" strokeWidth={1.4} fillOpacity={0} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 flex items-center gap-6 text-[12px] text-white/60">
                <span className="inline-flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#a3e635]" /> Positive</span>
                <span className="inline-flex items-center gap-2"><span className="w-2 h-2 rounded-full bg-[#ef4444]" /> Negative</span>
              </div>
            </GlassCard>

            {/* KEY MOMENTS */}
            <div data-testid="moments-list">
              <div className="overline mb-4">Key moments</div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                {topMoments.map((m) => (
                  <div
                    key={m.id}
                    className="flex items-center gap-4 rounded-lg border border-white/10 p-4"
                  >
                    <span
                      className="w-9 h-9 rounded-md flex items-center justify-center"
                      style={{ background: `${momentColor(m.type)}18`, border: `1px solid ${momentColor(m.type)}50` }}
                    >
                      <MomentIcon type={m.type} size={16} />
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="text-[14px] text-white font-semibold capitalize truncate">{m.type}</div>
                      <div className="text-[12px] text-white/60 truncate">{m.desc}</div>
                    </div>
                    <div className="text-[12px] font-bold text-white/80 shrink-0 tabular-nums">{m.minute}'</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
