import { Mail, MessageCircle, Sparkles, Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { useNavigate } from 'react-router-dom';

interface QuickActionItemProps {
  icon: React.ComponentType<{ className?: string }>;
  title: string;
  description: string;
  onClick: () => void;
  colorClass: string;
  bgClass: string;
}

function QuickActionItem({
  icon: Icon,
  title,
  description,
  onClick,
  colorClass,
  bgClass,
}: QuickActionItemProps) {
  return (
    <motion.button
      whileHover={{ scale: 1.01 }}
      whileTap={{ scale: 0.99 }}
      onClick={onClick}
      className="flex w-full items-start gap-4 rounded-xl border border-border bg-card p-4 text-left transition-all hover:border-primary/20 hover:shadow-md"
    >
      <div className={`rounded-xl p-3 ${bgClass} ${colorClass}`}>
        <Icon className="h-5 w-5" />
      </div>
      <div>
        <h4 className="text-sm font-semibold text-foreground">{title}</h4>
        <p className="mt-1 text-xs text-muted-foreground">{description}</p>
      </div>
    </motion.button>
  );
}

export function QuickActions() {
  const navigate = useNavigate();

  const actions = [
    {
      icon: Mail,
      title: 'Connect Gmail',
      description: 'Authorize Gmail accounts to allow AI scanning and replies.',
      onClick: () => navigate('/dashboard/connectors/gmail'),
      colorClass: 'text-red-400',
      bgClass: 'bg-red-400/10',
    },
    {
      icon: MessageCircle,
      title: 'Connect WhatsApp',
      description: 'Scan QR code to link WhatsApp device credentials.',
      onClick: () => navigate('/dashboard/connectors/whatsapp'),
      colorClass: 'text-green-400',
      bgClass: 'bg-green-400/10',
    },
    {
      icon: Sparkles,
      title: 'Ask AI Assistant',
      description: 'Interact with Ollama LLM to query summaries and generate drafts.',
      onClick: () => navigate('/dashboard/ai'),
      colorClass: 'text-primary',
      bgClass: 'bg-primary/10',
    },
    {
      icon: Search,
      title: 'Search Messages',
      description: 'Perform vector search queries across all messages.',
      onClick: () => navigate('/dashboard/search'),
      colorClass: 'text-amber-400',
      bgClass: 'bg-amber-400/10',
    },
  ];

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Quick Actions</h3>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        {actions.map((action) => (
          <QuickActionItem key={action.title} {...action} />
        ))}
      </div>
    </div>
  );
}
