import { KPI_TICKER } from "@/data/mock";

export default function Ticker() {
  const items = [...KPI_TICKER, ...KPI_TICKER];
  return (
    <div className="border-b border-white/10 bg-black/40 overflow-hidden" data-testid="kpi-ticker">
      <div className="ticker-track py-2">
        {items.map((it, i) => (
          <div key={i} className="flex items-center gap-3 px-8 whitespace-nowrap">
            <span className="w-1 h-1 rounded-full bg-white/60 pulse-dot" />
            <span className="overline">{it.k}</span>
            <span className="mono text-[12px] text-white">{it.v}</span>
            <span className="text-white/20">/</span>
          </div>
        ))}
      </div>
    </div>
  );
}
