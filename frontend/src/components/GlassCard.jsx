import { cn } from "@/lib/utils";

export default function GlassCard({ className = "", children, hover = true, ...rest }) {
  return (
    <div
      className={cn(
        "relative bg-white/[0.03] backdrop-blur-2xl border border-white/10",
        "shadow-[0_8px_32px_rgba(0,0,0,0.4)]",
        hover && "transition hover:border-white/25 hover:-translate-y-0.5",
        className
      )}
      {...rest}
    >
      {children}
    </div>
  );
}
