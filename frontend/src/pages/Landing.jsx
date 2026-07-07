import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Activity, Zap, Layers, Ticket } from "lucide-react";
import DataGlobe from "@/components/DataGlobe";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { FEATURES, BRAND } from "@/data/mock";

const FEATURE_META = [
  { icon: Activity, color: "#a3e635" },
  { icon: Zap,      color: "#ec4899" },
  { icon: Layers,   color: "#38bdf8" },
  { icon: Ticket,   color: "#f59e0b" },
];

export default function Landing() {
  return (
    <div data-testid="landing-page" className="relative">
      {/* HERO */}
      <section className="relative overflow-hidden min-h-[92vh] flex items-center">
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            backgroundImage:
              "url(https://images.unsplash.com/photo-1522778119026-d647f0596c20?auto=format&fit=crop&w=2400&q=80)",
            backgroundSize: "cover",
            backgroundPosition: "center",
          }}
        />
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "linear-gradient(180deg, rgba(6,10,23,0.82) 0%, rgba(6,10,23,0.7) 45%, rgba(6,10,23,0.98) 92%)",
          }}
        />
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(700px 400px at 12% 90%, rgba(163,230,53,0.18), transparent 60%), radial-gradient(700px 500px at 88% 20%, rgba(59,130,246,0.14), transparent 60%)",
          }}
        />
        <div className="grain absolute inset-0" />

        <div className="relative max-w-[1400px] mx-auto px-6 md:px-10 pt-14 pb-16 grid grid-cols-12 gap-6 items-center w-full">
          <div className="col-span-12 lg:col-span-6 z-10">
            <Reveal>
              <h1 className="display text-white leading-[0.9] text-[56px] md:text-[88px] lg:text-[100px]">
                THE PULSE<br />
                OF THE <span className="hero-gradient">PITCH</span>,<br />
                <span className="hero-gradient">MONETISED.</span>
              </h1>
            </Reveal>

            <Reveal delay={0.15}>
              <p className="text-white/70 mt-8 max-w-xl text-[15px] leading-relaxed">
                {BRAND.name} watches every fan reaction as it happens — goals, red cards, VAR,
                full-time — and turns each moment into a ready-to-deploy marketing play.
              </p>
            </Reveal>

            <Reveal delay={0.25}>
              <div className="mt-10">
                <Link
                  to="/heatmap"
                  data-testid="hero-get-started-button"
                  className="group inline-flex items-center gap-3 px-8 py-4 rounded-full text-[14px] font-bold tracking-tight bg-gradient-to-r from-[#a3e635] to-[#22c55e] text-[#052e16] hover:brightness-110 shadow-[0_10px_40px_-10px_rgba(163,230,53,0.6)] transition"
                >
                  Get Started
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition" />
                </Link>
              </div>
            </Reveal>
          </div>

          <div className="col-span-12 lg:col-span-6 relative h-[440px] md:h-[560px] lg:h-[640px]">
            <motion.div
              initial={{ opacity: 0, scale: 0.92 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
              className="absolute inset-0"
            >
              <DataGlobe />
            </motion.div>
            <div
              aria-hidden
              className="absolute top-4 right-4 text-white/60 tracking-[0.28em] uppercase text-[11px]"
            >
              World · Fan sentiment
            </div>
          </div>
        </div>

        <div
          aria-hidden
          className="absolute inset-x-0 bottom-0 h-24"
          style={{
            background:
              "linear-gradient(180deg, transparent, rgba(6,10,23,0.98))",
          }}
        />
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
