import { useMemo } from "react";
import { motion } from "framer-motion";
import { AreaChart, Area, ResponsiveContainer } from "recharts";
import type { NetworkSummary } from "../types";

interface BottomMetricsProps {
  summary: NetworkSummary | null;
}

// Dummy data generator for the sparklines to make them look alive
const generateSparklineData = (baseValue: number, volatility: number) => {
  return Array.from({ length: 15 }, (_, i) => ({
    name: i,
    value: Math.max(0, baseValue + (Math.random() - 0.5) * volatility),
  }));
};

export default function BottomMetrics({ summary }: BottomMetricsProps) {
  const coverage = summary ? Math.round(summary.network_coverage * 100) : 0;
  const avgCongestion = summary ? Math.round(summary.avg_congestion * 100) : 0;
  const activeAssets = summary?.active_assets || 0;

  // Memoize sparkline data so it doesn't jump crazily on every re-render
  // unless the summary actually changes.
  const chartData = useMemo(() => ({
    coverage: generateSparklineData(coverage || 50, 5),
    congestion: generateSparklineData(avgCongestion || 30, 15),
    assets: generateSparklineData(activeAssets || 100, 10),
    emissions: generateSparklineData(420, 20),
  }), [coverage, avgCongestion, activeAssets]);

  const cards = [
    {
      label: "NETWORK COVERAGE",
      value: `${coverage}%`,
      sub: "Connected Infrastructure",
      borderColor: "var(--color-teal)",
      valueColor: "var(--color-teal)",
      showBar: true,
      barValue: coverage,
      data: chartData.coverage,
    },
    {
      label: "AVG CONGESTION",
      value: `${avgCongestion}%`,
      sub: "Morning Peak Load",
      borderColor: "var(--color-orange)",
      valueColor: "var(--color-orange)",
      data: chartData.congestion,
    },
    {
      label: "ACTIVE ASSETS",
      value: String(activeAssets),
      sub: "Nodes + Edges Monitored",
      borderColor: "var(--color-blue)",
      valueColor: "var(--color-blue)",
      data: chartData.assets,
    },
    {
      label: "EMISSION SAVED",
      value: "420 T",
      sub: "Eco-Route Priority",
      borderColor: "var(--color-green)",
      valueColor: "var(--color-green)",
      data: chartData.emissions,
    },
  ];

  const containerVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { staggerChildren: 0.1, delayChildren: 0.2 }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0 }
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="flex items-stretch gap-4 px-6 py-3 border-t border-border-primary bg-bg-primary/95 backdrop-blur-md relative z-50 shadow-[0_-4px_20px_rgba(0,0,0,0.3)]"
    >
      {cards.map((card) => (
        <motion.div
          variants={itemVariants}
          key={card.label}
          className="flex-1 px-4 py-3 rounded-xl relative overflow-hidden bg-bg-secondary/60 border border-transparent hover:border-border-primary transition-colors group cursor-default"
          style={{
            borderLeft: `4px solid ${card.borderColor}`,
            boxShadow: `0 4px 20px -10px ${card.borderColor}40`
          }}
        >
          {/* Background Sparkline Chart */}
          <div className="absolute inset-0 opacity-20 pointer-events-none group-hover:opacity-30 transition-opacity duration-500 mt-6">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={card.data}>
                <defs>
                  <linearGradient id={`gradient-${card.label}`} x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor={card.borderColor} stopOpacity={0.8}/>
                    <stop offset="95%" stopColor={card.borderColor} stopOpacity={0}/>
                  </linearGradient>
                </defs>
                <Area type="monotone" dataKey="value" stroke={card.borderColor} fillOpacity={1} fill={`url(#gradient-${card.label})`} isAnimationActive={false} />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="relative z-10">
            <div
              className="text-[10px] font-semibold tracking-[0.2em] mb-1.5 text-text-secondary"
            >
              {card.label}
            </div>
            <div className="flex items-end gap-2">
              <span
                className="text-2xl font-bold font-mono tracking-tight"
                style={{ color: card.valueColor }}
              >
                {card.value}
              </span>
            </div>
            <div className="text-[10px] mt-1 text-text-muted">
              {card.sub}
            </div>
            {card.showBar && (
              <div className="mt-2 h-1.5 rounded-full overflow-hidden bg-border-primary/50 relative">
                <motion.div
                  initial={{ width: 0 }}
                  animate={{ width: `${card.barValue}%` }}
                  transition={{ duration: 1.5, ease: "easeOut" }}
                  className="absolute left-0 top-0 bottom-0 rounded-full"
                  style={{
                    background: `linear-gradient(90deg, ${card.borderColor}40, ${card.borderColor})`,
                    boxShadow: `0 0 10px ${card.borderColor}`
                  }}
                />
              </div>
            )}
          </div>
        </motion.div>
      ))}
    </motion.div>
  );
}
