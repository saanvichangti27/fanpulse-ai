import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { ArrowRight, Activity, Zap, Layers, Ticket } from "lucide-react";
import Football3D from "@/components/Football3D";
import Reveal from "@/components/Reveal";
import GlassCard from "@/components/GlassCard";
import { FEATURES, BRAND } from "@/data/mock";

const FEATURE_META = [
  { icon: Activity, tint: "from-[#a3e635]/25 to-[#22c55e]/5", color: "#a3e635" },
  { icon: Zap,      tint: "from-[#ec4899]/25 to-[#8b5cf6]/5", color: "#ec4899" },
  { icon: Layers,   tint: "from-[#3b82f6]/25 to-[#38bdf8]/5", color: "#3b82f6" },
  { icon: Ticket,   tint: "from-[#f59e0b]/25 to-[#ef4444]/5", color: "#f59e0b" },
];

export default function Landing() {
  return (
    <div data-testid="landing-page" className="relative">
      {/* HERO — stadium background */}
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
              "linear-gradient(180deg, rgba(6,10,23,0.72) 0%, rgba(6,10,23,0.6) 45%, rgba(6,10,23,0.95) 92%)",
          }}
        />
        <div
          aria-hidden
          className="absolute inset-0"
          style={{
            background:
              "radial-gradient(700px 400px at 10% 90%, rgba(163,230,53,0.22), transparent 60%), radial-gradient(700px 400px at 90% 15%, rgba(236,72,153,0.22), transparent 60%), radial-gradient(500px 300px at 60% 60%, rgba(59,130,246,0.18), transparent 60%)",
          }}
        />
        <div className="grain absolute inset-0" />

        <div className="relative max-w-[1400px] mx-auto px-6 md:px-10 pt-14 pb-16 grid grid-cols-12 gap-6 items-center w-full">
          <div className="col-span-12 lg:col-span-6 z-10">
            <Reveal>
              <h1 className="display text-white leading-[0.9] text-[56px] md:text-[92px] lg:text-[108px]">
                THE PULSE<br />
                OF THE <span className="gradient-lime">PITCH</span>,<br />
                <span className="gradient-fire">MONETISED.</span>
              </h1>
            </Reveal>

            <Reveal delay={0.2}>
              <p className="text-white/70 mt-8 max-w-xl text-[15px] leading-relaxed">
                {BRAND.name} watches every fan reaction as it happens — goals, red cards, VAR,
                full-time — and turns each moment into a ready-to-deploy marketing play.
              </p>
            </Reveal>

            <Reveal delay={0.3}>
              <div className="mt-10">
                <Link
                  to="/heatmap"
                  data-testid="hero-get-started-button"
                  className="group inline-flex items-center gap-3 px-8 py-4 rounded-full text-[14px] font-bold tracking-tight bg-gradient-to-r from-[#a3e635] via-[#22c55e] to-[#10b981] text-[#052e16] hover:brightness-110 shadow-[0_10px_40px_-10px_rgba(163,230,53,0.6)] transition"
                >
                  Get Started
                  <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition" />
                </Link>
              </div>
            </Reveal>
          </div>

          <div className="col-span-12 lg:col-span-6 relative h-[440px] md:h-[560px] lg:h-[640px]">
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 1.2, ease: [0.22, 1, 0.36, 1] }}
              className="absolute inset-0"
            >
              <Football3D />
            </motion.div>
            <div
              aria-hidden
              className="absolute inset-0 -z-10"
              style={{
                background:
                  "radial-gradient(closest-side, rgba(163,230,53,0.18), transparent 70%)",
              }}
            />
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
            <div className="section-topline flex items-baseline justify-between mb-14 flex-wrap gap-4">
              <div>
                <div className="overline">Modules</div>
                <h2 className="display text-white text-4xl md:text-5xl mt-2">
                  The <span className="gradient-lime">signal loop</span>.
                </h2>
              </div>
              <div className="text-[13px] text-white/50 hidden md:block">
                match &nbsp;›&nbsp; moment &nbsp;›&nbsp; strategy &nbsp;›&nbsp; ROI
              </div>
            </div>
          </Reveal>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {FEATURES.map((f, i) => {
              const meta = FEATURE_META[i] || FEATURE_META[0];
              const Icon = meta.icon;
              return (
                <Reveal key={f.code} delay={i * 0.08}>
                  <GlassCard
                    className={`relative p-6 h-full flex flex-col min-h-[240px] overflow-hidden rounded-2xl bg-gradient-to-br ${meta.tint}`}
                    hover
                  >
                    <div className="flex items-start justify-between">
                      <div
                        className="w-11 h-11 rounded-xl flex items-center justify-center"
                        style={{
                          background: `${meta.color}22`,
                          border: `1px solid ${meta.color}44`,
                        }}
                      >
                        <Icon size={22} style={{ color: meta.color }} />
                      </div>
                      <div className="overline">{f.code}</div>
                    </div>
                    <div className="mt-8">
                      <div className="display text-white text-2xl">{f.title}</div>
                      <div className="text-[13px] text-white/70 mt-3 leading-relaxed">{f.body}</div>
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
