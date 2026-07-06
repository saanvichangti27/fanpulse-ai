import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid,
  BarChart, Bar,
} from "recharts";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { MATCHES, SENTIMENT_TIMELINE, MOMENTS, TRENDING } from "@/data/mock";

const STATUS = {
  live: { label: "LIVE", tone: "text-white", dot: "bg-white pulse-dot" },
  upcoming: { label: "UPCOMING", tone: "text-white/60", dot: "bg-white/30" },
  finished: { label: "FT", tone: "text-white/40", dot: "bg-white/20" },
};

const MOMENT_ICON = {
  goal: "⚽",
  "red card": "▮",
  "VAR controversy": "?",
  "full time": "■",
  kickoff: "▶",
  "other surge": "≋",
};

function Gauge({ value, label }) {
  const pct = Math.max(0, Math.min(100, value));
  const r = 62;
  const c = 2 * Math.PI * r;
  const off = c * (1 - pct / 100);
  return (
    <div className="relative w-[160px] h-[160px]" data-testid="demand-gauge">
      <svg viewBox="0 0 160 160" className="w-full h-full -rotate-90">
        <circle cx="80" cy="80" r={r} stroke="rgba(255,255,255,0.08)" strokeWidth="6" fill="none" />
        <motion.circle
          cx="80" cy="80" r={r}
          stroke="#f8fafc" strokeWidth="6" fill="none"
          strokeLinecap="round"
          strokeDasharray={c}
          initial={{ strokeDashoffset: c }}
          animate={{ strokeDashoffset: off }}
          transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <div className="display metallic-text text-4xl">{pct}</div>
        <div className="overline mt-1">{label}</div>
      </div>
    </div>
  );
}

export default function Matches() {
  const [selectedId, setSelectedId] = useState(MATCHES[0].id);
  const selected = useMemo(() => MATCHES.find((m) => m.id === selectedId), [selectedId]);

  const roundedDate = (iso) => {
    const d = new Date(iso);
    return d.toLocaleString("en-GB", { day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
  };

  return (
    <div data-testid="matches-page" className="relative">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-14">
        <Reveal>
          <div className="flex items-baseline justify-between flex-wrap gap-3">
            <div>
              <div className="overline">03 · Match Console</div>
              <h1 className="display text-white text-5xl md:text-6xl mt-3 leading-[0.9]">
                Matches <span className="metallic-text">/ Ticket Demand</span>
              </h1>
            </div>
            <div className="mono text-[11px] text-white/50">Match history · Live · Upcoming</div>
          </div>
        </Reveal>

        <div className="mt-10 grid grid-cols-1 lg:grid-cols-12 gap-4">
          {/* SCHEDULE SIDEBAR */}
          <aside className="lg:col-span-4">
            <GlassCard className="p-4" hover={false} data-testid="match-schedule">
              <div className="flex items-baseline justify-between px-1 pb-3 border-b border-white/10">
                <div className="overline">Schedule</div>
                <div className="mono text-[10px] text-white/40">{MATCHES.length} fixtures</div>
              </div>
              <div className="mt-2 space-y-1.5">
                {MATCHES.map((m) => {
                  const isActive = m.id === selected.id;
                  const st = STATUS[m.status];
                  return (
                    <button
                      key={m.id}
                      data-testid={`match-item-${m.id}`}
                      onClick={() => setSelectedId(m.id)}
                      className={`w-full text-left p-3 border transition ${
                        isActive ? "border-white/50 bg-white/[0.04]" : "border-white/5 hover:border-white/20"
                      }`}
                    >
                      <div className="flex items-center justify-between">
                        <div className="mono text-[10px] tracking-widest text-white/50">
                          {m.tournament_stage}
                        </div>
                        <div className={`flex items-center gap-1.5 ${st.tone}`}>
                          <span className={`w-1.5 h-1.5 rounded-full ${st.dot}`} />
                          <span className="mono text-[10px] tracking-widest">{st.label}</span>
                        </div>
                      </div>
                      <div className="mt-2 flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="display text-white text-sm">{m.home_short}</span>
                          <span className="mono text-white/40 text-[11px]">vs</span>
                          <span className="display text-white text-sm">{m.away_short}</span>
                        </div>
                        {m.status !== "upcoming" && (
                          <div className="mono text-white text-sm">
                            {m.score.home}–{m.score.away}
                            {m.status === "live" && <span className="text-white/50 text-[10px] ml-1">{m.score.minute}'</span>}
                          </div>
                        )}
                      </div>
                      <div className="mt-2 flex items-center justify-between mono text-[10px] text-white/40">
                        <span>{roundedDate(m.kickoff)} · {m.venue.city}</span>
                        <span>DI {m.demand_index}</span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </GlassCard>

            {/* Trending */}
            <GlassCard className="mt-4 p-5" hover={false} data-testid="trending-panel">
              <div className="flex items-baseline justify-between">
                <div className="overline">Trending topics</div>
                <div className="mono text-[10px] text-white/40">last 5m</div>
              </div>
              <ul className="mt-4 space-y-2">
                {TRENDING.map((t, i) => (
                  <li key={t.topic} className="flex items-center justify-between mono text-[12px] border-b border-white/5 pb-1.5">
                    <span className="flex items-center gap-3">
                      <span className="text-white/40 w-4">{String(i + 1).padStart(2, "0")}</span>
                      <span className="text-white">{t.topic}</span>
                    </span>
                    <span className="flex items-center gap-2">
                      <span className="text-white/50">{t.mentions.toLocaleString()}</span>
                      <span className={`w-4 text-center ${
                        t.dir === "up" ? "text-white" : t.dir === "down" ? "text-white/30" : "text-white/50"
                      }`}>
                        {t.dir === "up" ? "▲" : t.dir === "down" ? "▼" : "▬"}
                      </span>
                    </span>
                  </li>
                ))}
              </ul>
            </GlassCard>
          </aside>

          {/* MAIN — DEMAND + STATS */}
          <div className="lg:col-span-8 space-y-4">
            {/* HEAD */}
            <GlassCard className="p-6 md:p-8" hover={false} data-testid="match-detail-head">
              <div className="flex items-start justify-between flex-wrap gap-6">
                <div>
                  <div className="overline">{selected.tournament_stage} · {selected.venue.city}</div>
                  <div className="mt-3 flex items-baseline gap-4 flex-wrap">
                    <div className="display text-white text-4xl md:text-5xl">{selected.home}</div>
                    <div className="mono text-white/40 text-sm">vs</div>
                    <div className="display text-white text-4xl md:text-5xl">{selected.away}</div>
                  </div>
                  <div className="mt-3 mono text-[12px] text-white/50">
                    Capacity {selected.venue.capacity.toLocaleString()} · Kick-off {roundedDate(selected.kickoff)}
                  </div>
                </div>

                <div className="flex items-center gap-8">
                  <Gauge value={selected.demand_index} label="Demand" />
                  <div className="space-y-3">
                    <div>
                      <div className="overline">Sellout probability</div>
                      <div className="display metallic-text text-3xl mt-1">{Math.round(selected.sellout_prob * 100)}%</div>
                    </div>
                    <div>
                      <div className="overline">Excitement</div>
                      <div className="display text-white text-2xl mt-1">{selected.excitement}<span className="text-white/40 text-base">/100</span></div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Baseline vs current re-forecast */}
              <div className="mt-6 border-t border-white/10 pt-5 grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <div className="overline">Baseline forecast</div>
                  <div className="mono text-white text-2xl mt-1">{selected.baseline_forecast}</div>
                </div>
                <div>
                  <div className="overline">Live re-forecast</div>
                  <div className="mono text-white text-2xl mt-1 flex items-baseline gap-2">
                    {selected.demand_index}
                    <span className={`text-sm ${selected.demand_index >= selected.baseline_forecast ? "text-white" : "text-white/40"}`}>
                      {selected.demand_index >= selected.baseline_forecast ? "+" : ""}
                      {selected.demand_index - selected.baseline_forecast}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="overline">Trigger</div>
                  <div className="mono text-white/80 text-[12px] mt-1 leading-relaxed">{selected.forecast_trigger}</div>
                </div>
              </div>
            </GlassCard>

            {/* SENTIMENT TIMELINE */}
            <GlassCard className="p-6" hover={false} data-testid="sentiment-timeline">
              <div className="flex items-baseline justify-between mb-4">
                <div className="overline">Sentiment timeline</div>
                <div className="mono text-[10px] text-white/40">buckets · 5-min</div>
              </div>
              <div className="w-full h-[240px]">
                <ResponsiveContainer>
                  <AreaChart data={SENTIMENT_TIMELINE} margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
                    <defs>
                      <linearGradient id="g-pos" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="0%" stopColor="#f8fafc" stopOpacity={0.7} />
                        <stop offset="100%" stopColor="#f8fafc" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid stroke="rgba(255,255,255,0.05)" vertical={false} />
                    <XAxis dataKey="minute" tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} />
                    <YAxis tick={{ fill: "rgba(255,255,255,0.5)", fontSize: 10, fontFamily: "JetBrains Mono" }} tickLine={false} axisLine={false} />
                    <Tooltip
                      contentStyle={{
                        background: "rgba(5,9,20,0.9)",
                        border: "1px solid rgba(255,255,255,0.15)",
                        color: "#fff",
                        fontFamily: "JetBrains Mono",
                        fontSize: 11,
                      }}
                      labelStyle={{ color: "rgba(255,255,255,0.6)" }}
                    />
                    <Area type="monotone" dataKey="positive" stroke="#f8fafc" strokeWidth={1.5} fill="url(#g-pos)" />
                    <Area type="monotone" dataKey="negative" stroke="rgba(239,68,68,0.6)" strokeWidth={1} fillOpacity={0} />
                    <Area type="monotone" dataKey="neutral" stroke="rgba(148,163,184,0.5)" strokeWidth={1} fillOpacity={0} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              <div className="mt-3 flex items-center gap-4 mono text-[11px] text-white/50">
                <span className="inline-flex items-center gap-2"><span className="w-2 h-2 bg-white" /> Positive</span>
                <span className="inline-flex items-center gap-2"><span className="w-2 h-2 bg-red-500/60" /> Negative</span>
                <span className="inline-flex items-center gap-2"><span className="w-2 h-2 bg-white/40" /> Neutral</span>
              </div>
            </GlassCard>

            {/* MOMENTS + DRIVERS */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <GlassCard className="p-6" hover={false} data-testid="moments-list">
                <div className="overline mb-4">Detected moments</div>
                <ul className="space-y-2">
                  {MOMENTS.map((m) => (
                    <li key={m.id} className="flex items-start gap-3 border-b border-white/5 pb-2.5">
                      <span className="mono text-white/40 text-[11px] w-8">{String(m.minute).padStart(2, "0")}'</span>
                      <span className="mono text-white/70 w-4">{MOMENT_ICON[m.type] || "•"}</span>
                      <div className="flex-1">
                        <div className="mono text-[12px] text-white capitalize">{m.type}</div>
                        <div className="mono text-[11px] text-white/50">{m.desc}</div>
                      </div>
                      <span className="mono text-[10px] text-white/40 shrink-0">{m.volume.toLocaleString()}</span>
                    </li>
                  ))}
                </ul>
              </GlassCard>

              <GlassCard className="p-6" hover={false} data-testid="drivers-chart">
                <div className="overline mb-4">Demand drivers</div>
                <div className="w-full h-[220px]">
                  <ResponsiveContainer>
                    <BarChart data={selected.drivers} layout="vertical" margin={{ top: 4, right: 10, left: 20, bottom: 0 }}>
                      <CartesianGrid stroke="rgba(255,255,255,0.05)" horizontal={false} />
                      <XAxis type="number" hide />
                      <YAxis
                        type="category"
                        dataKey="factor"
                        tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 11, fontFamily: "JetBrains Mono" }}
                        tickLine={false}
                        axisLine={false}
                        width={100}
                      />
                      <Tooltip
                        contentStyle={{
                          background: "rgba(5,9,20,0.9)",
                          border: "1px solid rgba(255,255,255,0.15)",
                          fontFamily: "JetBrains Mono",
                          fontSize: 11,
                        }}
                      />
                      <Bar dataKey="weight" fill="#e2e8f0" radius={[0, 0, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </GlassCard>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
