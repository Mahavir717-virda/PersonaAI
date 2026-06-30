import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: LucideIcon;
  iconColor?: string;
  index?: number;
}

export function StatsCard({
  title,
  value,
  change,
  changeType = 'positive',
  icon: Icon,
  iconColor = 'text-primary',
  index = 0,
}: StatsCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      whileHover={{ y: -2, transition: { duration: 0.2 } }}
      className="group rounded-xl border border-border bg-card p-6 transition-all hover:border-primary/20 hover:shadow-lg hover:shadow-primary/5"
    >
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-muted-foreground">{title}</p>
        <div
          className={cn(
            'rounded-lg bg-primary/10 p-2 transition-colors group-hover:bg-primary/15',
          )}
        >
          <Icon className={cn('h-5 w-5', iconColor)} />
        </div>
      </div>
      <p className="mt-3 text-3xl font-bold text-foreground">{value}</p>
      {change && (
        <p
          className={cn(
            'mt-1 text-sm',
            changeType === 'positive' && 'text-success',
            changeType === 'negative' && 'text-destructive',
            changeType === 'neutral' && 'text-muted-foreground',
          )}
        >
          {change}
        </p>
      )}
    </motion.div>
  );
}
