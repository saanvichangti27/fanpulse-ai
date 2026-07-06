import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Radio } from "lucide-react";
import Football3D from "@/components/Football3D";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { FEATURES, BRAND } from "@/data/mock";

export default function Landing() {
  return (
    <div data-testid="landing-page" className="relative">
      {/* HERO */}
      <section className="relative overflow-hidden">
        {/* Background stadium mask */}
        <div
          aria-hidden
          className="absolute inset-0 opacity-[0.18]"
          style={{
            backgroundImage:
              "url(https://images.pexels.com/photos/35898730/pexels-photo-35898730.jpeg)",
            backgroundSize: "cover",
            backgroundPosition: "center",
            filter: "grayscale(1) contrast(1.05)",
          }}
        />
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(5,9,20,0.85) 0%, rgba(5,9,20,0.7) 40%, #050914 90%)",
          }}
        />
        <div className="grain absolute inset-0" />

        <div className="relative max-w-[1400px] mx-auto px-6 md:px-10 pt-16 md:pt-24 pb-16 grid grid-cols-12 gap-6 items-center">
          {/* Left copy */}
          <div className="col-span-12 lg:col-span-6 z-10">
            <Reveal>
              <div className="flex items-center gap-3 mb-8">
                <span className="inline-flex items-center gap-2 border border-white/15 px-3 py-1">
                  <Radio className="w-3 h-3 text-white" />
                  <span className="overline">Signal · Live</span>
                </span>
                <span className="overline">A / 2026 · Semi-Final Cycle</span>
              </div>
            </Reveal>

            <Reveal delay={0.1}>
              <h1 className="display text-white leading-[0.88] text-[56px] md:text-[86px] lg:text-[104px]">
                THE PULSE<br />
                <span className="metallic-text">OF THE PITCH,</span><br />
                MONETISED.
              </h1>
            </Reveal>

            <Reveal delay={0.2}>
              <p className="mono text-white/60 mt-8 max-w-xl text-[13px] leading-relaxed">
                {BRAND.name} watches every fan reaction as it happens. Goals, red cards, VAR,
                full-time — turned into ready-to-deploy marketing plays. Segment. Channel.
                Copy. ROI. Evidence.
              </p>
            </Reveal>

            <Reveal delay={0.3}>
              <div className="mt-10 flex flex-col sm:flex-row items-start sm:items-center gap-4">
                <Link
                  to="/matches"
                  data-testid="hero-get-started-button"
                  className="group relative inline-flex items-center gap-3 bg-white text-[#050914] px-7 py-4 mono text-[12px] tracking-[0.24em] uppercase font-medium hover:bg-white/90 transition"
                >
                  Get Started
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition" />
                </Link>
                <Link
                  to="/heatmap"
                  data-testid="hero-secondary-cta"
                  className="inline-flex items-center gap-2 border border-white/20 hover:border-white/60 text-white px-6 py-4 mono text-[12px] tracking-[0.24em] uppercase transition"
                >
                  See the Heatmap
                </Link>
              </div>
            </Reveal>

            <Reveal delay={0.5}>
              <div className="mt-14 grid grid-cols-3 gap-6 max-w-lg">
                {[
                  { k: "Excitement", v: "87" },
                  { k: "Positive", v: "68.3%" },
                  { k: "Msg / min", v: "2,411" },
                ].map((s) => (
                  <div key={s.k} className="border-l border-white/15 pl-4">
                    <div className="overline">{s.k}</div>
                    <div className="mono text-white text-2xl mt-2">{s.v}</div>
                  </div>
                ))}
              </div>
            </Reveal>
          </div>

          {/* Right 3D */}
          <div className="col-span-12 lg:col-span-6 relative h-[420px] md:h-[560px] lg:h-[640px]">
            <motion.div
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
              className="absolute inset-0"
            >
              <Football3D />
            </motion.div>

            {/* Chrome corner brackets */}
            {["top-0 left-0", "top-0 right-0", "bottom-0 left-0", "bottom-0 right-0"].map((pos, i) => (
              <div key={i} className={`absolute ${pos} w-10 h-10 pointer-events-none`}>
                <div className={`absolute ${i < 2 ? "top-0" : "bottom-0"} ${i % 2 === 0 ? "left-0" : "right-0"} w-6 h-px bg-white/40`} />
                <div className={`absolute ${i < 2 ? "top-0" : "bottom-0"} ${i % 2 === 0 ? "left-0" : "right-0"} w-px h-6 bg-white/40`} />
              </div>
            ))}

            <div className="absolute bottom-4 left-4 flex items-center gap-2 mono text-[11px] text-white/60">
              <span className="w-1.5 h-1.5 bg-white rounded-full pulse-dot" />
              WEBGL · 60fps · rig 01
            </div>
            <div className="absolute top-4 right-4 mono text-[11px] text-white/50 tracking-widest">
              N° 01 / MATCH-BALL
            </div>
          </div>
        </div>
      </section>

      {/* MANIFESTO STRIP */}
      <section className="relative border-y border-white/10 bg-black/30">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-6 flex flex-col md:flex-row md:items-baseline md:justify-between gap-4">
          <div className="overline">Manifesto — 01</div>
          <p className="display text-white text-2xl md:text-3xl max-w-4xl leading-tight tracking-tight">
            Every number carries evidence. Every campaign carries a moment. Every moment carries a countdown.
          </p>
          <div className="mono text-[11px] text-white/40">// no live sends — labels only</div>
        </div>
      </section>

      {/* FEATURES */}
      <section className="relative">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20 md:py-28">
          <Reveal>
            <div className="flex items-baseline justify-between mb-12">
              <div>
                <div className="overline">Modules — 02</div>
                <h2 className="display text-white text-4xl md:text-5xl mt-3">The signal loop.</h2>
              </div>
              <div className="mono text-[12px] text-white/40 hidden md:block">
                match → moment → strategy → ROI
              </div>
            </div>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((f, i) => (
              <Reveal key={f.code} delay={i * 0.08}>
                <GlassCard className="p-6 h-full flex flex-col justify-between min-h-[220px]">
                  <div className="flex items-start justify-between">
                    <div className="overline">{f.code}</div>
                    <div className="w-2 h-2 bg-white/70 pulse-dot" />
                  </div>
                  <div>
                    <div className="display text-white text-2xl mt-8">{f.title}</div>
                    <div className="mono text-[12px] text-white/55 mt-3 leading-relaxed">{f.body}</div>
                  </div>
                </GlassCard>
              </Reveal>
            ))}
          </div>
        </div>
      </section>

      {/* BIG STAT BAND */}
      <section className="border-y border-white/10 bg-black/30">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-16 grid grid-cols-2 md:grid-cols-4 gap-8">
          {[
            { k: "Fixtures tracked", v: "42" },
            { k: "Moments / match", v: "18.4" },
            { k: "Segments live", v: "5" },
            { k: "Avg. ROAS uplift", v: "×3.7" },
          ].map((s, i) => (
            <Reveal key={s.k} delay={i * 0.06}>
              <div>
                <div className="overline">{s.k}</div>
                <div className="display metallic-text text-5xl md:text-6xl mt-2">{s.v}</div>
              </div>
            </Reveal>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="relative">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-24 md:py-32 grid grid-cols-12 gap-6">
          <Reveal className="col-span-12 md:col-span-7">
            <div className="overline">CTA — 03</div>
            <h2 className="display text-white text-4xl md:text-6xl mt-4 leading-[0.95]">
              Wire your brand<br />into the <span className="metallic-text">90 minutes</span>.
            </h2>
            <p className="mono text-white/55 mt-6 max-w-lg text-[13px] leading-relaxed">
              Frontend preview only. Backend endpoints are separate — this UI is ready to be wired
              to the FanPulse REST layer.
            </p>
          </Reveal>
          <Reveal className="col-span-12 md:col-span-5" delay={0.1}>
            <GlassCard className="p-8">
              <div className="overline">Console access</div>
              <div className="display text-white text-3xl mt-3">Open the match console</div>
              <div className="mt-6 space-y-2 mono text-[12px] text-white/55">
                <div className="flex justify-between border-b border-white/5 py-2"><span>Live matches</span><span className="text-white">3</span></div>
                <div className="flex justify-between border-b border-white/5 py-2"><span>Auto-cards inbox</span><span className="text-white">14 new</span></div>
                <div className="flex justify-between py-2"><span>Signal freshness</span><span className="text-white">2s</span></div>
              </div>
              <Link
                to="/matches"
                data-testid="cta-open-console"
                className="mt-8 inline-flex items-center gap-3 bg-white text-[#050914] px-6 py-3 mono text-[12px] tracking-[0.24em] uppercase hover:bg-white/90 transition"
              >
                Open Console <ArrowRight className="w-4 h-4" />
              </Link>
            </GlassCard>
          </Reveal>
        </div>
      </section>
    </div>
  );
}
