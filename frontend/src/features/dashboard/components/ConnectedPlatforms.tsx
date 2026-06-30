import { useEffect, useState } from 'react';
import { Mail, MessageCircle, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';
import apiClient from '@/services/api.client';

interface PlatformItemProps {
  name: string;
  icon: React.ComponentType<{ className?: string }>;
  status: 'connected' | 'disconnected' | 'error';
  lastSync?: string;
  colorClass: string;
}

function PlatformItem({
  name,
  icon: Icon,
  status,
  lastSync,
  colorClass,
}: PlatformItemProps) {
  return (
    <div className="flex items-center justify-between rounded-xl border border-border bg-card p-4">
      <div className="flex items-center gap-3">
        <div className={`rounded-lg bg-muted p-2 ${colorClass}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div>
          <h4 className="text-sm font-semibold text-foreground">{name}</h4>
          {lastSync && (
            <p className="text-xs text-muted-foreground">Sync: {lastSync}</p>
          )}
        </div>
      </div>
      <div className="flex items-center gap-1.5">
        {status === 'connected' && (
          <>
            <CheckCircle2 className="h-4 w-4 text-green-400" />
            <span className="text-xs font-medium text-green-400">Connected</span>
          </>
        )}
        {status === 'disconnected' && (
          <>
            <AlertCircle className="h-4 w-4 text-muted-foreground" />
            <span className="text-xs font-medium text-muted-foreground">Disconnected</span>
          </>
        )}
        {status === 'error' && (
          <>
            <ShieldAlert className="h-4 w-4 text-destructive" />
            <span className="text-xs font-medium text-destructive">Error</span>
          </>
        )}
      </div>
    </div>
  );
}

export function ConnectedPlatforms() {
  const [platforms, setPlatforms] = useState<Array<{
    name: string;
    icon: typeof Mail;
    status: 'connected' | 'disconnected' | 'error';
    lastSync?: string;
    colorClass: string;
  }>>([]);

  useEffect(() => {
    const fetchPlatforms = async () => {
      try {
        const response = await apiClient.get('/api/v1/connectors');
        const active = response.data.data?.active || [];
        const mapped = [
          {
            name: 'Gmail Integration',
            icon: Mail,
            status: active.some((item: any) => item.platform === 'gmail' && item.state === 'connected') ? 'connected' as const : 'disconnected' as const,
            lastSync: active.find((item: any) => item.platform === 'gmail')?.last_sync || undefined,
            colorClass: 'text-red-400',
          },
          {
            name: 'WhatsApp Integration',
            icon: MessageCircle,
            status: active.some((item: any) => item.platform === 'whatsapp' && item.state === 'connected') ? 'connected' as const : 'disconnected' as const,
            lastSync: active.find((item: any) => item.platform === 'whatsapp')?.last_sync || undefined,
            colorClass: 'text-green-400',
          },
        ];
        setPlatforms(mapped);
      } catch (error) {
        console.error('Failed to load connected platforms', error);
      }
    };

    fetchPlatforms();
  }, []);

  return (
    <div className="space-y-4">
      <h3 className="text-sm font-semibold text-foreground">Connected Platforms</h3>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-1">
        {platforms.map((platform) => (
          <PlatformItem key={platform.name} {...platform} />
        ))}
      </div>
    </div>
  );
}
