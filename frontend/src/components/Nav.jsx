import { NavLink, Link } from "react-router-dom";
import { NAV_LINKS, BRAND } from "@/data/mock";
import { motion } from "framer-motion";

export default function Nav() {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="sticky top-0 z-40 backdrop-blur-xl bg-[#050914]/70 border-b border-white/10"
      data-testid="site-nav"
    >
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group" data-testid="brand-logo">
          <div className="w-8 h-8 relative">
            <div className="absolute inset-0 rounded-full border border-white/30 group-hover:border-white/70 transition" />
            <div className="absolute inset-[6px] rounded-full bg-white/80 group-hover:bg-white transition" />
          </div>
          <div className="leading-tight">
            <div className="display text-[15px] text-white tracking-tight">{BRAND.name}</div>
            <div className="overline">{BRAND.version} — signal engine</div>
          </div>
        </Link>

        <nav className="hidden md:flex items-center gap-8">
          {NAV_LINKS.map((l) => (
            <NavLink
              key={l.path}
              to={l.path}
              end={l.path === "/"}
              data-testid={`nav-${l.label.toLowerCase()}`}
              className={({ isActive }) =>
                `group flex items-baseline gap-2 text-[13px] tracking-wide transition ${
                  isActive ? "text-white" : "text-white/50 hover:text-white"
                }`
              }
            >
              <span className="overline">{l.code}</span>
              <span>{l.label}</span>
            </NavLink>
          ))}
        </nav>

        <Link
          to="/matches"
          data-testid="nav-cta"
          className="hidden md:inline-flex items-center gap-2 border border-white/20 hover:border-white/70 text-white text-[12px] tracking-[0.2em] uppercase px-4 py-2 transition"
        >
          Open Console <span className="text-white/50">→</span>
        </Link>
      </div>
    </motion.header>
  );
}
