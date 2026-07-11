import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  Mail,
  MessageCircle,
  MessageSquare,
  Globe,
  Settings,
  RefreshCw,
  Power,
  HelpCircle,
  Plus,
  ShieldCheck,
} from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import { PageTransition } from '@/components/animations/PageTransition';
import { useNotificationStore } from '@/store/notification.store';
import apiClient, { readPersistedAccessToken } from '@/services/api.client';
import { useAuthStore } from '@/store/auth.store';

interface ConnectorItem {
  id?: string;
  platform: string;
  name: string;
  state: string; // connected, disconnected, syncing, authorizing, error, expired, reconnect_required
  settings: Record<string, any>;
  last_sync: string | null;
  last_sync_status: string;
  icon?: string;
  capabilities?: Record<string, boolean>;
}

const iconMap: Record<string, any> = {
  gmail: Mail,
  whatsapp: MessageCircle,
  slack: MessageSquare,
  outlook: Mail,
  teams: MessageSquare,
  telegram: Globe,
  discord: Globe,
};

export function ConnectorsPage() {
  const [connectors, setConnectors] = useState<ConnectorItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncingMap, setSyncingMap] = useState<Record<string, boolean>>({});
  const [showWizard, setShowWizard] = useState(false);
  const [selectedPlatform, setSelectedPlatform] = useState<any>(null);
  const [phoneId, setPhoneId] = useState('');
  const [waToken, setWaToken] = useState('');
  const [connecting, setConnecting] = useState(false);
  const { addNotification } = useNotificationStore();
  const navigate = useNavigate();
  const { isAuthenticated, isLoading } = useAuthStore();

  const fetchConnectors = async () => {
    try {
      const response = await apiClient.get('/api/v1/connectors');
      const { active, available } = response.data.data;

      const activeMap = new Map(active.map((c: any) => [c.platform, c]));
      const combined: ConnectorItem[] = available.map((av: any) => {
        const act: any = activeMap.get(av.id) || {};
        return {
          id: act.id,
          platform: av.id,
          name: av.name,
          state: act.state || 'disconnected',
          settings: act.settings || {},
          last_sync: act.last_sync || null,
          last_sync_status: act.last_sync_status || 'never',
          icon: av.icon,
          capabilities: av.capabilities,
        };
      });

      setConnectors(combined);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      fetchConnectors();
    }
    const params = new URLSearchParams(window.location.search);
    if (params.get('success') === 'true') {
      addNotification({
        title: 'Platform Connected',
        message: 'Your Gmail connection has been successfully established.',
        type: 'success',
      });
      // Remove the query param from the URL
      window.history.replaceState({}, document.title, window.location.pathname);
    }
  }, [isLoading, isAuthenticated]);

  const handleSync = async (conn: ConnectorItem) => {
    if (conn.state === 'disconnected') return;
    const accessToken = useAuthStore.getState().accessToken || readPersistedAccessToken();
    if (!accessToken) {
      addNotification({
        title: 'Session Required',
        message: 'Please sign in again before syncing connectors.',
        type: 'error',
      });
      return;
    }

    setSyncingMap((prev) => ({ ...prev, [conn.platform]: true }));
    try {
      if (conn.platform === 'gmail') {
        await apiClient.get('/api/v1/connectors/gmail/messages');
        addNotification({
          title: 'Inbox Refreshed',
          message: `Loaded the latest stored Gmail messages for ${conn.name}.`,
          type: 'success',
        });
      } else {
        const response = await apiClient.post(`/api/v1/connectors/${conn.platform}/sync`);
        const resData = response.data.data;
        if (resData.status === 'success') {
          addNotification({
            title: 'Sync Complete',
            message: `Successfully synchronized ${resData.messages_imported} messages from ${conn.name}.`,
            type: 'success',
          });
        } else {
          addNotification({
            title: 'Sync Failed',
            message: resData.error || `Failed to sync ${conn.name}.`,
            type: 'error',
          });
        }
      }
      fetchConnectors();
    } catch {
      addNotification({
        title: 'Sync Error',
        message: conn.platform === 'gmail' ? `Unable to reload Gmail inbox for ${conn.name}.` : `An error occurred while syncing ${conn.name}.`,
        type: 'error',
      });
    } finally {
      setSyncingMap((prev) => ({ ...prev, [conn.platform]: false }));
    }
  };

  const handleConnectClick = async (conn: ConnectorItem) => {
    if (conn.platform === 'gmail') {
      try {
        const daysInput = prompt(
          "How much email history would you like PersonaAI to analyze?\n\nEnter number of days (e.g. 30, 90, 180) or leave blank/0 for 'All':",
          "30"
        );
        if (daysInput === null) return; // User cancelled
        const syncRangeDays = parseInt(daysInput.trim(), 10) || 0;

        const postAuthRedirectUri = `${window.location.origin}/dashboard/connectors`;
        let authUrlPath = `/api/v1/connectors/gmail/auth-url?post_auth_redirect_uri=${encodeURIComponent(postAuthRedirectUri)}`;
        if (syncRangeDays > 0) {
          authUrlPath += `&sync_range_days=${syncRangeDays}`;
        }

        const response = await apiClient.get(authUrlPath);
        const authUrl = response.data.data.authorization_url;
        window.location.href = authUrl;
      } catch (err) {
        console.error(err);
        addNotification({
          title: 'OAuth Error',
          message: 'Failed to retrieve Google authorization link.',
          type: 'error',
        });
      }
    } else {
      setSelectedPlatform(conn);
      setShowWizard(true);
    }
  };

  const simulateConnect = async (platform: string, authData: any) => {
    setConnecting(true);
    try {
      await apiClient.post(`/api/v1/connectors/${platform}/connect`, {
        auth_data: authData,
      });
      addNotification({
        title: 'Platform Connected',
        message: `Your ${platform.toUpperCase()} connection has been successfully established.`,
        type: 'success',
      });
      setShowWizard(false);
      setPhoneId('');
      setWaToken('');
      fetchConnectors();
    } catch (err) {
      console.error(err);
      addNotification({
        title: 'Connection Failed',
        message: 'Failed to establish connection to platform provider.',
        type: 'error',
      });
    } finally {
      setConnecting(false);
    }
  };

  const handleDisconnect = async (conn: ConnectorItem) => {
    if (confirm(`Are you sure you want to disconnect ${conn.name}?`)) {
      try {
        await apiClient.post(`/api/v1/connectors/${conn.platform}/disconnect`);
        addNotification({
          title: 'Platform Disconnected',
          message: `Successfully disconnected your ${conn.name} account.`,
          type: 'info',
        });
        fetchConnectors();
      } catch (err) {
        console.error(err);
        addNotification({
          title: 'Error',
          message: `Failed to disconnect ${conn.name}.`,
          type: 'error',
        });
      }
    }
  };

  if (loading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <RefreshCw className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <PageTransition className="space-y-6">
      <PageHeader
        title="Platform Connectors"
        description="Link your Gmail, WhatsApp, and other platform communications to our central indexing and AI engine."
      />

      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {connectors.map((conn) => {
          const PlatformIcon = iconMap[conn.platform] || HelpCircle;
          const isSyncing = syncingMap[conn.platform];
          const isConnected = conn.state === 'connected';

          return (
            <motion.div
              key={conn.platform}
              whileHover={{ y: -2 }}
              className="flex flex-col justify-between rounded-xl border border-border bg-card p-6 shadow-sm hover:border-primary/20"
            >
              <div>
                <div className="flex items-center justify-between mb-4">
                  <div className="flex items-center gap-3">
                    <div className={`rounded-xl bg-muted p-3 ${isConnected ? 'text-primary' : 'text-muted-foreground'}`}>
                      <PlatformIcon className="h-6 w-6" />
                    </div>
                    <div>
                      <h4 className="text-base font-semibold text-foreground">{conn.name}</h4>
                      <p className="text-xs text-muted-foreground">Version {conn.settings.version || '1.0.0'}</p>
                    </div>
                  </div>

                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium capitalize ${
                    conn.state === 'connected' ? 'bg-green-500/10 text-green-400' :
                    conn.state === 'syncing' ? 'bg-primary/10 text-primary animate-pulse' :
                    conn.state === 'error' ? 'bg-destructive/10 text-destructive' :
                    'bg-muted text-muted-foreground'
                  }`}>
                    {conn.state}
                  </span>
                </div>

                <div className="space-y-2 mb-6">
                  <div className="flex justify-between text-xs">
                    <span className="text-muted-foreground">Sync Status</span>
                    <span className="text-foreground capitalize">{conn.last_sync_status}</span>
                  </div>
                  {conn.last_sync && (
                    <div className="flex justify-between text-xs">
                      <span className="text-muted-foreground">Last synchronized</span>
                      <span className="text-foreground">
                        {new Date(conn.last_sync).toLocaleDateString()} {new Date(conn.last_sync).toLocaleTimeString()}
                      </span>
                    </div>
                  )}
                </div>
              </div>

              <div className="flex gap-2">
                {isConnected ? (
                  <>
                    <button
                      onClick={() => handleSync(conn)}
                      disabled={isSyncing}
                      className="inline-flex flex-1 items-center justify-center gap-1.5 rounded-lg border border-border bg-background py-2 text-xs font-semibold text-foreground transition-all hover:bg-muted disabled:opacity-50"
                    >
                      <RefreshCw className={`h-3.5 w-3.5 ${isSyncing ? 'animate-spin' : ''}`} />
                      Sync
                    </button>
                    <button
                      onClick={() => navigate(`/dashboard/connectors/${conn.platform}`)}
                      className="inline-flex rounded-lg border border-border bg-background p-2 text-foreground transition-all hover:bg-muted"
                      title="Connector Details"
                    >
                      <Settings className="h-3.5 w-3.5" />
                    </button>
                    <button
                      onClick={() => handleDisconnect(conn)}
                      className="inline-flex rounded-lg border border-border bg-background p-2 text-destructive transition-all hover:bg-destructive/10"
                      title="Disconnect Account"
                    >
                      <Power className="h-3.5 w-3.5" />
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => handleConnectClick(conn)}
                    className="inline-flex w-full items-center justify-center gap-1.5 rounded-lg bg-primary py-2.5 text-xs font-semibold text-primary-foreground shadow-sm transition-all hover:bg-primary/95"
                  >
                    <Plus className="h-4 w-4" />
                    Connect Account
                  </button>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Connection Wizard Modal for WhatsApp and other custom setups */}
      {showWizard && selectedPlatform && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-md rounded-xl border border-border bg-card p-6 shadow-2xl animate-fade-in">
            <h3 className="text-lg font-bold text-foreground mb-1">
              Configure {selectedPlatform.name}
            </h3>
            <p className="text-xs text-muted-foreground mb-4">
              Enter your provider account settings. Credentials are stored securely.
            </p>

            <div className="space-y-4 mb-6">
              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Phone Number ID</label>
                <input
                  type="text"
                  value={phoneId}
                  onChange={(e) => setPhoneId(e.target.value)}
                  placeholder="e.g. 1094857732"
                  className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                />
              </div>

              <div className="space-y-1">
                <label className="text-xs font-semibold text-foreground">Authorization Token / API Key</label>
                <input
                  type="password"
                  value={waToken}
                  onChange={(e) => setWaToken(e.target.value)}
                  placeholder="Enter system access token"
                  className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2">
              <button
                onClick={() => setShowWizard(false)}
                className="rounded-lg border border-border bg-background px-4 py-2 text-sm font-semibold text-foreground transition-all hover:bg-muted"
              >
                Cancel
              </button>
              <button
                onClick={() => simulateConnect(selectedPlatform.platform, { phone_number_id: phoneId, token: waToken })}
                disabled={connecting || !phoneId || !waToken}
                className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/95 disabled:opacity-50"
              >
                <ShieldCheck className="h-4 w-4" />
                {connecting ? 'Connecting...' : 'Authorize'}
              </button>
            </div>
          </div>
        </div>
      )}
    </PageTransition>
  );
}
export default ConnectorsPage;
