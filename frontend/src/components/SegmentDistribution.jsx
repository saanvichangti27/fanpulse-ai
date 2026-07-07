import { motion } from "framer-motion";
import { FAN_SEGMENTS } from "@/data/mock";

/**
 * Fan Segmentation Distribution diagram — a horizontal stacked share bar
 * with connecting lines to legend blocks below (matches the sketch: title
 * on top with a decorative rule + connecting flow to segment items).
 */
export default function SegmentDistribution() {
  let cumulative = 0;
  return (
    <div className="relative" data-testid="segment-distribution">
      {/* Stacked bar */}
      <div className="relative h-14 w-full rounded-md overflow-hidden bg-white/[0.03] border border-white/10">
        {FAN_SEGMENTS.map((s) => {
          const width = s.share * 100;
          const left = cumulative;
          cumulative += width;
          return (
            <motion.div
              key={s.id}
              data-testid={`distribution-block-${s.id}`}
              initial={{ width: 0 }}
              whileInView={{ width: `${width}%` }}
              viewport={{ once: true }}
              transition={{ duration: 1, ease: [0.22, 1, 0.36, 1] }}
              className="absolute top-0 bottom-0 flex items-center justify-center text-[10px] font-bold text-black/80 tracking-wider uppercase"
              style={{ left: `${left}%`, background: s.color }}
            >
              {width > 10 ? `${Math.round(width)}%` : ""}
            </motion.div>
          );
        })}
      </div>

      {/* Connector rails */}
      <div className="grid grid-cols-5 gap-3 mt-0">
        {FAN_SEGMENTS.map((s) => (
          <div key={s.id} className="flex flex-col items-center">
            <div className="w-px h-6" style={{ background: s.color }} />
            <div
              className="w-full text-center py-2 border-t"
              style={{ borderColor: s.color }}
            >
              <div className="flex items-center justify-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full" style={{ background: s.color }} />
                <span className="text-[11px] font-semibold text-white tracking-tight">
                  {s.name}
                </span>
              </div>
              <div className="mt-1 text-[10px] text-white/50">
                {(s.size / 1000).toFixed(1)}k
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
