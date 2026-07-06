import { BRAND } from "@/data/mock";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 mt-24" data-testid="site-footer">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-10 grid grid-cols-1 md:grid-cols-4 gap-8">
        <div className="col-span-2">
          <div className="display text-white text-2xl">{BRAND.name}</div>
          <p className="mono text-[12px] text-white/50 mt-3 max-w-md leading-relaxed">
            {BRAND.tagline} A real-time marketing decision engine wired to live football signal.
          </p>
        </div>
        <div>
          <div className="overline mb-3">Product</div>
          <ul className="space-y-2 mono text-[12px] text-white/60">
            <li>Live Pulse</li>
            <li>Heatmap</li>
            <li>Strategies</li>
            <li>Match Console</li>
          </ul>
        </div>
        <div>
          <div className="overline mb-3">Signals</div>
          <ul className="space-y-2 mono text-[12px] text-white/60">
            <li>Reddit · YouTube · News</li>
            <li>Replay fixtures</li>
            <li>Sim X/Twitter (labeled)</li>
            <li>Poll interval — 2s</li>
          </ul>
        </div>
      </div>
      <div className="border-t border-white/5">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-4 flex items-center justify-between">
          <span className="overline">© 2026 · {BRAND.name} · Frontend Preview</span>
          <span className="mono text-[11px] text-white/40">Data is mock · Wire to REST later</span>
        </div>
      </div>
    </footer>
  );
}
