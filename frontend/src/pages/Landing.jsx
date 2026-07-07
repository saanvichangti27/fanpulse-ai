import { useEffect, useRef } from "react";
import { Link } from "react-router-dom";
import { ArrowRight, Activity, Zap, Layers, Ticket } from "lucide-react";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import DataGlobe from "@/components/DataGlobe";
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
        <div 
          aria-hidden 
          className="absolute inset-0 bg-[#060a17] bg-cover bg-center" 
          style={{ backgroundImage: "linear-gradient(rgba(6,10,23,0.7), rgba(6,10,23,0.9)), url('https://images.unsplash.com/photo-1522778119026-d647f0596c20?q=80&w=2070&auto=format&fit=crop')" }} 
        />

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
            <div className="mt-16 mx-auto h-[400px] md:h-[500px] w-full max-w-4xl relative">
              <DataGlobe />
            </div>
          </Reveal>
        </div>
      </section>
    </div>
  );
}
