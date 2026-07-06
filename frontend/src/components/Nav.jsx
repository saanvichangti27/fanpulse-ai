import { NavLink, Link } from "react-router-dom";
import { NAV_LINKS, BRAND } from "@/data/mock";
import { motion } from "framer-motion";

export default function Nav() {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="sticky top-0 z-40 backdrop-blur-xl bg-[#060a17]/70 border-b border-white/10"
      data-testid="site-nav"
    >
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-3 group" data-testid="brand-logo">
          <div className="relative w-9 h-9">
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-[#a3e635] via-[#22c55e] to-[#3b82f6] blur-md opacity-70 group-hover:opacity-100 transition" />
            <div className="absolute inset-0 rounded-full bg-gradient-to-br from-[#a3e635] to-[#22c55e] flex items-center justify-center">
              <div className="w-2 h-2 rounded-full bg-[#060a17]" />
            </div>
          </div>
          <div className="leading-tight">
            <div className="display text-[16px] text-white tracking-tight">{BRAND.name}</div>
            <div className="overline text-[9px]">Signal engine</div>
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
                `relative text-[14px] font-medium tracking-tight transition ${
                  isActive ? "text-white" : "text-white/55 hover:text-white"
                }`
              }
            >
              {({ isActive }) => (
                <>
                  {l.label}
                  {isActive && (
                    <motion.span
                      layoutId="nav-underline"
                      className="absolute -bottom-2 left-0 right-0 h-[2px] bg-gradient-to-r from-[#a3e635] to-[#22c55e]"
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

        <Link
          to="/heatmap"
          data-testid="nav-cta"
          className="hidden md:inline-flex items-center gap-2 text-[13px] font-semibold tracking-tight px-5 py-2.5 rounded-full bg-gradient-to-r from-[#a3e635] to-[#22c55e] text-[#052e16] hover:brightness-110 transition"
        >
          Get Started <span>→</span>
        </Link>
      </div>
    </motion.header>
  );
}
