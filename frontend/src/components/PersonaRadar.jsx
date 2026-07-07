import { RadarChart, PolarGrid, PolarAngleAxis, Radar, ResponsiveContainer } from "recharts";

export default function PersonaRadar({ segment, color = "#a3e635" }) {
  const data = [
    { axis: "Engage", value: segment.engagement },
    { axis: "Value",  value: Math.min(100, Math.round((segment.annual_value / 800) * 100)) },
    { axis: "Share",  value: Math.min(100, Math.round(segment.share * 300)) },
    { axis: "Live",   value: Math.min(100, Math.round(segment.engagement * 0.85)) },
    { axis: "Retain", value: 100 - segment.churn },
  ];
  return (
    <div className="w-full h-[200px]" data-testid="persona-radar">
      <ResponsiveContainer>
        <RadarChart data={data} outerRadius="72%">
          <PolarGrid stroke="rgba(255,255,255,0.14)" />
          <PolarAngleAxis
            dataKey="axis"
            tick={{ fill: "rgba(255,255,255,0.6)", fontSize: 10 }}
          />
          <Radar
            dataKey="value"
            stroke={color}
            fill={color}
            fillOpacity={0.45}
            strokeWidth={1.5}
            isAnimationActive
          />
        </RadarChart>
      </ResponsiveContainer>
    </div>
  );
}
