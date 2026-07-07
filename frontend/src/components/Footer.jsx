import { BRAND } from "@/data/mock";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 mt-24" data-testid="site-footer">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-10 flex flex-col md:flex-row md:items-end md:justify-between gap-8">
        <div>
          <div className="flex items-center gap-2">
            <img src="logo.png" alt="FanPulseAI Logo" className="w-8 h-8 object-contain" />
            <div className="display text-white text-2xl">{BRAND.name}</div>
          </div>
          <p className="text-[13px] text-white/55 mt-3 max-w-md leading-relaxed">
            Real-time marketing intelligence for the beautiful game.
          </p>
        </div>
        <div className="flex flex-col md:items-end gap-2">
          <div className="overline">Modules</div>
          <div className="flex gap-6 text-[13px] text-white/70">
            <span>Heatmap</span>
            <span>Strategies</span>
            <span>Matches</span>
          </div>
        </div>
      </div>
      <div className="border-t border-white/5">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-4 flex items-center justify-between">
          <span className="overline">© 2026 · {BRAND.name}</span>
        </div>
      </div>
    </footer>
  );
}
