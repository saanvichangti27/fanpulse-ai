/**
 * Compact 3-bar mini viz for persona cards.
 * Bars: Engagement, Value (log-normalized to $800 cap), Retention (100-churn).
 */
export default function MetricBars({ engagement, value, churn, color = "#a3e635" }) {
  const items = [
    { k: "ENGAGE", v: engagement, max: 100 },
    { k: "VALUE",  v: Math.min(100, Math.round((value / 800) * 100)), max: 100 },
    { k: "RETAIN", v: 100 - churn, max: 100 },
  ];
  return (
    <div className="grid grid-cols-3 gap-2" data-testid="metric-bars">
      {items.map((i) => (
        <div key={i.k} className="flex flex-col items-stretch">
          <div className="relative h-12 w-full bg-white/[0.04] rounded-sm overflow-hidden">
            <div
              className="absolute bottom-0 left-0 right-0 transition-all"
              style={{
                height: `${(i.v / i.max) * 100}%`,
                background: `linear-gradient(180deg, ${color} 0%, ${color}55 100%)`,
                boxShadow: `0 0 12px ${color}66`,
              }}
            />
          </div>
          <div className="mt-1 flex items-baseline justify-between">
            <span className="text-[9px] text-white/45 tracking-widest">{i.k}</span>
            <span className="text-[10px] text-white font-semibold">{i.v}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
