import { ReactNode } from "react";
import { motion } from "framer-motion";
import NeoCard from "./NeoCard";

interface StatCardProps {
  label: string;
  value: string | number;
  icon: ReactNode;
  accent?: string;
  delay?: number;
}

export default function StatCard({ label, value, icon, accent = "#9C8CD4", delay = 0 }: StatCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay }}
    >
      <NeoCard className="flex items-center gap-4">
        <div
          className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl shadow-neo-flat"
          style={{ background: `${accent}22`, color: accent }}
        >
          {icon}
        </div>
        <div>
          <p className="text-2xl font-bold text-ink dark:text-dark-ink">{value}</p>
          <p className="text-xs font-medium text-ink/60 dark:text-dark-ink/60">{label}</p>
        </div>
      </NeoCard>
    </motion.div>
  );
}
