import { useMemo, useState } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip, CartesianGrid } from "recharts";
import { MessageCircle, Repeat2, Heart, TrendingUp, TrendingDown, Minus } from "lucide-react";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import Flag from "@/components/Flag";
import { MATCHES, SENTIMENT_TIMELINE, TRENDING, LIVE_FEED } from "@/data/mock";

const STATUS_META = {
  live:     { label: "LIVE",     color: "#a3e635", dotClass: "bg-[#a3e635] pulse-dot" },
  upcoming: { label: "UPCOMING", color: "#38bdf8", dotClass: "bg-[#38bdf8]" },
  finished: { label: "FT",       color: "#94a3b8", dotClass: "bg-white/30" },
};

const SENTIMENT_TONE = {
  positive: "#a3e635",
  negative: "#ef4444",
  neutral:  "#94a3b8",
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

function DirIcon({ dir }) {
  if (dir === "up") return <TrendingUp size={12} className="text-[#a3e635]" />;
  if (dir === "down") return <TrendingDown size={12} className="text-[#ef4444]" />;
  return <Minus size={12} className="text-white/50" />;
}

function formatCount(n) {
  if (n >= 1000) return `${(n / 1000).toFixed(1)}K`;
  return `${n}`;
}

function TrendingTopics() {
  return (
    <div data-testid="trending-topics">
      <div className="overline mb-4">Trending topics</div>
      <div className="flex flex-wrap gap-2">
        {TRENDING.map((t, i) => (
          <span
            key={t.topic}
            className="inline-flex items-center gap-2 border border-white/10 rounded-full px-3.5 py-2 text-[13px] text-white/85 hover:border-white/30 transition"
          >
            <span className="text-white/40 text-[10px] tabular-nums w-4">{String(i + 1).padStart(2, "0")}</span>
            <span className="font-semibold">{t.topic}</span>
            <DirIcon dir={t.dir} />
            <span className="text-white/45 text-[11px] tabular-nums">{formatCount(t.mentions)}</span>
          </span>
        ))}
      </div>
    </div>
  );
}

function FeedItem({ item }) {
  const tone = SENTIMENT_TONE[item.sentiment] || "#94a3b8";
  return (
    <article className="rounded-xl border border-white/10 hover:border-white/25 transition p-4 flex gap-3" data-testid={`feed-item-${item.id}`}>
      <div
        className="w-10 h-10 rounded-full shrink-0 flex items-center justify-center text-[12px] font-bold text-[#052e16]"
        style={{ background: `linear-gradient(135deg, ${tone}, #22c55e)` }}
      >
        {item.initials}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 text-[13px]">
          <span className="text-white font-semibold truncate">{item.author}</span>
          <span className="text-white/45 truncate">{item.handle}</span>
          <span className="text-white/25">·</span>
          <span className="text-white/45 whitespace-nowrap">{item.time}</span>
          <Flag iso2={item.iso2} size={14} className="ml-auto shrink-0" />
        </div>
        <p className="text-[14px] text-white/90 mt-1 leading-snug break-words">{item.text}</p>
        <div className="mt-3 flex items-center gap-6 text-[11px] text-white/50">
          <span className="inline-flex items-center gap-1.5"><MessageCircle size={12} />{item.replies}</span>
          <span className="inline-flex items-center gap-1.5"><Repeat2 size={12} />{item.reposts}</span>
          <span className="inline-flex items-center gap-1.5"><Heart size={12} />{item.likes.toLocaleString()}</span>
          <span
            className="ml-auto text-[10px] font-semibold tracking-widest uppercase"
            style={{ color: tone }}
          >
            {item.sentiment}
          </span>
        </div>
      </div>
    </article>
  );
}

export default function Matches() {
  const [selectedId, setSelectedId] = useState(MATCHES[0].id);
  const selected = useMemo(() => MATCHES.find((m) => m.id === selectedId), [selectedId]);
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

            {/* TRENDING TOPICS + LIVE FEED */}
            <TrendingTopics />

            <div data-testid="live-feed">
              <div className="flex items-center justify-between mb-4">
                <div className="overline">Live feed</div>
                <span className="text-[11px] text-white/55 flex items-center gap-1.5">
                  <span className="w-1.5 h-1.5 rounded-full bg-[#a3e635] pulse-dot" />
                  streaming
                </span>
              </div>
              <div className="space-y-3">
                {LIVE_FEED.map((item) => (
                  <FeedItem key={item.id} item={item} />
                ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
