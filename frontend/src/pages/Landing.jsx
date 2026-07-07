import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Activity, Zap, Layers, Ticket } from "lucide-react";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { FEATURES, BRAND } from "@/data/mock";

const FEATURE_META = [
  { icon: Activity, color: "#a3e635" },
  { icon: Zap,      color: "#ec4899" },
  { icon: Layers,   color: "#38bdf8" },
  { icon: Ticket,   color: "#f59e0b" },
];

const SIGNAL_SOURCES = ["Reddit", "YouTube", "News", "Live Match Feed", "Fan Simulation"];

export default function Landing() {
  const heroRef = useRef(null);

  useEffect(() => {
    const el = heroRef.current;
    if (!el) return;
    const onMove = (e) => {
      const r = el.getBoundingClientRect();
      el.style.setProperty("--spot-x", `${e.clientX - r.left}px`);
      el.style.setProperty("--spot-y", `${e.clientY - r.top}px`);
    };
    el.addEventListener("mousemove", onMove);
    return () => el.removeEventListener("mousemove", onMove);
  }, []);

  return (
    <div data-testid="landing-page" className="relative">
      {/* HERO */}
      <section
        ref={heroRef}
        className="relative overflow-hidden min-h-[92vh] flex items-center"
        style={{ "--spot-x": "50%", "--spot-y": "40%" }}
        data-testid="hero-section"
      >
        {/* base */}
        <div aria-hidden className="absolute inset-0 bg-[#060a17]" />

        {/* dot grid */}
        <div
          aria-hidden
          className="absolute inset-0 opacity-[0.35]"
          style={{
            backgroundImage:
              "radial-gradient(rgba(255,255,255,0.16) 1px, transparent 1px)",
            backgroundSize: "26px 26px",
            maskImage:
              "radial-gradient(ellipse 80% 60% at center, black 30%, transparent 78%)",
            WebkitMaskImage:
              "radial-gradient(ellipse 80% 60% at center, black 30%, transparent 78%)",
          }}
        />

        {/* spotlight follows cursor */}
        <div
          aria-hidden
          className="absolute inset-0 pointer-events-none"
          style={{
            background:
              "radial-gradient(500px circle at var(--spot-x) var(--spot-y), rgba(163,230,53,0.22), rgba(59,130,246,0.10) 30%, transparent 55%)",
            transition: "background 60ms linear",
          }}
        />

        <div className="relative w-full max-w-[1000px] mx-auto px-6 md:px-10 text-center pt-14 pb-16">
          <Reveal>
            <div className="overline flex items-center justify-center gap-2 mb-8">
              <span className="w-1.5 h-1.5 rounded-full bg-[#a3e635] pulse-dot" />
              Real-time fan intelligence
            </div>
          </Reveal>

          <Reveal delay={0.1}>
            <h1 className="display text-white leading-[0.94] text-[52px] md:text-[76px] lg:text-[92px]">
              Turn every moment<br />
              into a <span className="hero-gradient">campaign</span>.
            </h1>
          </Reveal>

          <Reveal delay={0.2}>
            <p className="text-white/65 mt-8 max-w-xl mx-auto text-[15px] leading-relaxed">
              {BRAND.name} listens to the roar of the crowd — every goal, red card and
              full-time whistle — and hands you the ready-to-deploy marketing play.
            </p>
          </Reveal>

          <Reveal delay={0.3}>
            <div className="mt-10 flex items-center justify-center gap-3 flex-wrap">
              <Link
                to="/heatmap"
                data-testid="hero-get-started-button"
                className="group inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-[13px] font-semibold bg-white text-[#060a17] hover:bg-[#a3e635] transition"
              >
                Start building
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition" />
              </Link>
              <Link
                to="/matches"
                data-testid="hero-secondary-cta"
                className="inline-flex items-center gap-2 px-7 py-3.5 rounded-full text-[13px] font-semibold border border-white/25 text-white/90 hover:border-white/70 hover:bg-white/[0.04] transition"
              >
                Explore matches
              </Link>
            </div>
          </Reveal>

          <Reveal delay={0.45}>
            <div className="mt-16 mx-auto max-w-3xl">
              <div className="rounded-full border border-white/12 bg-white/[0.03] backdrop-blur px-6 md:px-8 py-3.5 flex items-center justify-between gap-5 overflow-x-auto">
                <span className="overline whitespace-nowrap shrink-0">Signal sources</span>
                <div className="w-px h-4 bg-white/15 shrink-0" />
                {SIGNAL_SOURCES.map((s) => (
                  <span key={s} className="text-[13px] text-white/65 whitespace-nowrap">{s}</span>
                ))}
              </div>
            </div>
          </Reveal>
        </div>
      </section>

      {/* SIGNAL LOOP */}
      <section className="relative">
        <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-20 md:py-28">
          <Reveal>
            <div className="section-topline mb-14">
              <div className="overline">Modules</div>
              <h2 className="display text-white text-4xl md:text-5xl mt-2">
                The signal loop.
              </h2>
            </div>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((f, i) => {
              const meta = FEATURE_META[i] || FEATURE_META[0];
              const Icon = meta.icon;
              return (
                <Reveal key={f.code} delay={i * 0.08}>
                  <GlassCard
                    className="relative p-6 h-full flex flex-col min-h-[220px] overflow-hidden rounded-xl border border-white/10"
                    hover
                  >
                    <div
                      className="w-11 h-11 rounded-lg flex items-center justify-center"
                      style={{ background: `${meta.color}1a`, border: `1px solid ${meta.color}44` }}
                    >
                      <Icon size={20} style={{ color: meta.color }} />
                    </div>
                    <div className="mt-6">
                      <div className="display text-white text-xl">{f.title}</div>
                      <div className="text-[13px] text-white/65 mt-3 leading-relaxed">{f.body}</div>
                    </div>
                  </GlassCard>
                </Reveal>
              );
            })}
          </div>
        </div>
      </section>
    </div>
  );
}
