import { BRAND } from "@/data/mock";

export default function Footer() {
  return (
    <footer className="border-t border-white/10 mt-24" data-testid="site-footer">
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-10 flex justify-end gap-8">
        <div className="flex gap-6 text-[13px] text-white/70">
          <span>Heatmap</span>
          <span>Strategies</span>
          <span>Matches</span>
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
