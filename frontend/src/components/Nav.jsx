import { NavLink, Link } from "react-router-dom";
import { NAV_LINKS, BRAND } from "@/data/mock";
import { motion } from "framer-motion";

export default function Nav() {
  return (
    <motion.header
      initial={{ y: -20, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.6, ease: [0.22, 1, 0.36, 1] }}
      className="sticky top-0 z-40 backdrop-blur-xl bg-[#060a17]/75 border-b border-white/10"
      data-testid="site-nav"
    >
      <div className="max-w-[1400px] mx-auto px-6 md:px-10 py-4 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2.5 group" data-testid="brand-logo">
          <div className="relative w-8 h-8 rounded-full overflow-hidden flex items-center justify-center bg-transparent">
            <img src="logo.png" alt="FanPulseAI Logo" className="w-full h-full object-contain" />
          </div>
          <span className="display text-white text-[17px] tracking-tight">{BRAND.name}</span>
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
                      className="absolute -bottom-2 left-0 right-0 h-[2px] bg-[#a3e635]"
                    />
                  )}
                </>
              )}
            </NavLink>
          ))}
        </nav>

      </div>
    </motion.header>
  );
}
