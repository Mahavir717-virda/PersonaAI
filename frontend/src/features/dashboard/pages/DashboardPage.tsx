import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutDashboard, Mail, MessageCircle, CheckSquare, Sparkles, PlusCircle } from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import { StatsCard } from '../components/StatsCard';
import { ActivityFeed } from '../components/ActivityFeed';
import { QuickActions } from '../components/QuickActions';
import { ConnectedPlatforms } from '../components/ConnectedPlatforms';
import { PageTransition } from '@/components/animations/PageTransition';
import apiClient from '@/services/api.client';

interface DashboardSummary {
  total?: number;
  gmail?: number;
  whatsapp?: number;
  total_tasks?: number;
  ai_summaries?: number;
}

export function DashboardPage() {
  const navigate = useNavigate();
  const [summary, setSummary] = useState<DashboardSummary>({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchSummary = async () => {
      try {
        const response = await apiClient.get('/api/v1/communications/summary');
        const data = response.data.data || {};
        setSummary({
          total: data.total || 0,
          gmail: data.gmail || 0,
          whatsapp: data.whatsapp || 0,
          total_tasks: data.total_tasks || 0,
          ai_summaries: data.ai_summaries || 0,
        });
      } catch (error) {
        console.error('Failed to load dashboard summary', error);
      } finally {
        setLoading(false);
      }
    };

    fetchSummary();
  }, []);

  const stats = [
    {
      title: 'Total Communications',
      value: summary.total ?? 0,
      change: 'Live data from your integrations',
      changeType: 'positive' as const,
      icon: LayoutDashboard,
      iconColor: 'text-primary',
    },
    {
      title: 'Gmail Messages',
      value: summary.gmail ?? 0,
      change: 'From connected Gmail account',
      changeType: 'positive' as const,
      icon: Mail,
      iconColor: 'text-red-400',
    },
    {
      title: 'WhatsApp Messages',
      value: summary.whatsapp ?? 0,
      change: 'From connected WhatsApp account',
      changeType: 'positive' as const,
      icon: MessageCircle,
      iconColor: 'text-green-400',
    },
    {
      title: 'Pending Tasks',
      value: summary.total_tasks ?? 0,
      change: 'Extracted from your communications',
      changeType: 'negative' as const,
      icon: CheckSquare,
      iconColor: 'text-amber-400',
    },
    {
      title: 'AI Summaries Generated',
      value: summary.ai_summaries ?? 0,
      change: 'Generated from recent activity',
      changeType: 'neutral' as const,
      icon: Sparkles,
      iconColor: 'text-violet-400',
    },
  ];

  return (
    <PageTransition className="space-y-6">
      <PageHeader
        title="Dashboard"
        description="Overview of your connected communication platforms and AI workflows."
        action={
          <button
            onClick={() => navigate('/dashboard/connectors')}
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90"
          >
            <PlusCircle className="h-4 w-4" />
            Connect Platform
          </button>
        }
      />

      {/* Stats Grid */}
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {stats.map((stat, i) => (
          <StatsCard key={stat.title} index={i} {...stat} />
        ))}
      </div>

      {loading && (
        <p className="text-sm text-muted-foreground">Loading your live dashboard data…</p>
      )}

      {/* Main Content Layout */}
      <div className="grid gap-6 lg:grid-cols-3">
        {/* Left/Middle column: Activity feed */}
        <div className="lg:col-span-2 space-y-6">
          <ActivityFeed />
        </div>

        {/* Right column: Actions & Platforms */}
        <div className="space-y-6">
          <QuickActions />
          <ConnectedPlatforms />
        </div>
      </div>
    </PageTransition>
  );
}
export default DashboardPage;
