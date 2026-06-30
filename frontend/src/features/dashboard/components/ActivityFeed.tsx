import { motion } from 'framer-motion';
import { Mail, MessageCircle, Sparkles, CheckSquare, Settings2 } from 'lucide-react';
import type { ActivityItem } from '@/types';
import { cn } from '@/lib/utils';

const iconMap = {
  gmail: Mail,
  whatsapp: MessageCircle,
  ai: Sparkles,
  task: CheckSquare,
  system: Settings2,
};

const colorMap = {
  gmail: 'text-red-400 bg-red-400/10',
  whatsapp: 'text-green-400 bg-green-400/10',
  ai: 'text-primary bg-primary/10',
  task: 'text-amber-400 bg-amber-400/10',
  system: 'text-muted-foreground bg-muted',
};

const sampleActivities: ActivityItem[] = [
  {
    id: '1',
    type: 'gmail',
    title: 'New email from Sarah Chen',
    description: 'Q3 Product Roadmap Review — 3 attachments',
    timestamp: new Date(Date.now() - 300000).toISOString(),
    read: false,
  },
  {
    id: '2',
    type: 'ai',
    title: 'AI Summary Generated',
    description: 'Morning digest for 12 conversations across 2 platforms',
    timestamp: new Date(Date.now() - 1800000).toISOString(),
    read: false,
  },
  {
    id: '3',
    type: 'whatsapp',
    title: 'Team Group Message',
    description: 'Alex: "Meeting pushed to 3pm, will send updated agenda"',
    timestamp: new Date(Date.now() - 3600000).toISOString(),
    read: true,
  },
  {
    id: '4',
    type: 'task',
    title: 'Task Completed',
    description: 'Follow up with design team re: dashboard mockups',
    timestamp: new Date(Date.now() - 7200000).toISOString(),
    read: true,
  },
  {
    id: '5',
    type: 'gmail',
    title: 'Newsletter from TechCrunch',
    description: 'Your daily digest — AI & Machine Learning highlights',
    timestamp: new Date(Date.now() - 10800000).toISOString(),
    read: true,
  },
];

function timeAgo(timestamp: string): string {
  const diff = Date.now() - new Date(timestamp).getTime();
  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.floor(hours / 24)}d ago`;
}

export function ActivityFeed() {
  return (
    <div className="rounded-xl border border-border bg-card">
      <div className="flex items-center justify-between border-b border-border px-6 py-4">
        <h3 className="text-sm font-semibold text-foreground">Recent Activity</h3>
        <button className="text-xs text-primary hover:underline">View All</button>
      </div>
      <div className="divide-y divide-border">
        {sampleActivities.map((item, i) => {
          const Icon = iconMap[item.type];
          return (
            <motion.div
              key={item.id}
              initial={{ opacity: 0, x: -10 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: i * 0.05 }}
              className={cn(
                'flex items-start gap-3 px-6 py-4 transition-colors hover:bg-muted/50',
                !item.read && 'bg-primary/5',
              )}
            >
              <div className={cn('mt-0.5 rounded-lg p-2', colorMap[item.type])}>
                <Icon className="h-4 w-4" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium text-foreground">{item.title}</p>
                <p className="text-xs text-muted-foreground truncate">
                  {item.description}
                </p>
              </div>
              <span className="shrink-0 text-xs text-muted-foreground">
                {timeAgo(item.timestamp)}
              </span>
            </motion.div>
          );
        })}
      </div>
    </div>
  );
}
