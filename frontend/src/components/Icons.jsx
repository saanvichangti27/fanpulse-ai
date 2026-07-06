import {
  Bell, Instagram, Youtube, Mail,
  UtensilsCrossed, Shirt, CupSoda, PlayCircle, Sparkles,
  Zap, Flag as FlagIcon, AlertOctagon, CircleAlert, Timer, Trophy,
} from "lucide-react";

const CHANNEL = {
  push:      { icon: Bell,      color: "#a3e635" },
  instagram: { icon: Instagram, color: "#ec4899" },
  youtube:   { icon: Youtube,   color: "#ef4444" },
  email:     { icon: Mail,      color: "#3b82f6" },
};

const INDUSTRY = {
  food_qsr:     { icon: UtensilsCrossed, color: "#f59e0b" },
  sports_merch: { icon: Shirt,           color: "#a3e635" },
  beverages:    { icon: CupSoda,         color: "#38bdf8" },
  streaming:    { icon: PlayCircle,      color: "#ec4899" },
  creators:     { icon: Sparkles,        color: "#fbbf24" },
};

const MOMENT = {
  goal:               { icon: Trophy,       color: "#a3e635" },
  "red card":         { icon: AlertOctagon, color: "#ef4444" },
  "VAR controversy":  { icon: CircleAlert,  color: "#f59e0b" },
  "full time":        { icon: Timer,        color: "#94a3b8" },
  kickoff:            { icon: FlagIcon,     color: "#38bdf8" },
  "other surge":      { icon: Zap,          color: "#a78bfa" },
};

export function ChannelIcon({ id, size = 14, className = "" }) {
  const conf = CHANNEL[id];
  if (!conf) return null;
  const Icon = conf.icon;
  return <Icon size={size} className={className} style={{ color: conf.color }} />;
}
export const channelColor = (id) => CHANNEL[id]?.color || "#a3e635";

export function IndustryIcon({ id, size = 16, className = "" }) {
  const conf = INDUSTRY[id];
  if (!conf) return null;
  const Icon = conf.icon;
  return <Icon size={size} className={className} style={{ color: conf.color }} />;
}
export const industryColor = (id) => INDUSTRY[id]?.color || "#a3e635";

export function MomentIcon({ type, size = 14, className = "" }) {
  const conf = MOMENT[type] || MOMENT["other surge"];
  const Icon = conf.icon;
  return <Icon size={size} className={className} style={{ color: conf.color }} />;
}
export const momentColor = (type) => (MOMENT[type] || MOMENT["other surge"]).color;
