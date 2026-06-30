import { useEffect, useMemo, useState } from 'react';
import {
  RefreshCw,
  Mail,
  Search,
  Filter,
  Eye,
  Paperclip,
  AlertCircle,
  CalendarDays,
  Inbox,
  UserRound,
  AtSign,
  Tags,
  MessageSquareText,
  X,
} from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import { PageTransition } from '@/components/animations/PageTransition';
import apiClient, { readPersistedAccessToken } from '@/services/api.client';
import { useAuthStore } from '@/store/auth.store';

interface GmailMessageItem {
  id: string;
  communication_id: string;
  platform_message_id: string;
  thread_id: string | null;
  subject: string | null;
  body: string;
  sender_name: string;
  sender_address: string;
  recipient_address: string;
  created_at: string;
  attachments: Array<{ id: string; name: string; size_bytes?: number | null }>;
  labels: string[];
  snippet: string | null;
  unread: boolean;
}

export function GmailPage() {
  const [messages, setMessages] = useState<GmailMessageItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [exclude, setExclude] = useState('');
  const [selected, setSelected] = useState<GmailMessageItem | null>(null);

  const filteredMessages = useMemo(() => {
    const normalizedSearch = search.trim().toLowerCase();
    const normalizedExclude = exclude.trim().toLowerCase();
    return messages.filter((message) => {
      const searchable = `${message.subject || ''} ${message.sender_name} ${message.sender_address} ${message.recipient_address} ${message.snippet || ''}`.toLowerCase();
      return (
        (!normalizedSearch || searchable.includes(normalizedSearch)) &&
        (!normalizedExclude || !searchable.includes(normalizedExclude))
      );
    });
  }, [messages, search, exclude]);

  const fetchMessages = async (refresh = false) => {
    setLoading(true);
    setError(null);
    try {
      const response = await apiClient.get(
        `/api/v1/connectors/gmail/messages${refresh ? '?refresh=true' : ''}`,
      );
      const data = response.data.data?.messages || [];
      setMessages(data);
    } catch (fetchError) {
      console.error('Failed to load Gmail messages', fetchError);
      setError('Unable to load Gmail messages. Try syncing the inbox again.');
    } finally {
      setLoading(false);
    }
  };

  const syncGmailInbox = async () => {
    const accessToken = useAuthStore.getState().accessToken || readPersistedAccessToken();
    if (!accessToken) {
      setError('You are signed out or your session has not loaded yet. Please sign in again, then sync Gmail.');
      return;
    }

    setSyncing(true);
    setError(null);
    try {
      await fetchMessages(true);
    } finally {
      setSyncing(false);
    }
  };

  useEffect(() => {
    fetchMessages();
  }, []);

  const handleSubmit = (event: React.FormEvent) => {
    event.preventDefault();
    fetchMessages();
  };

  return (
    <PageTransition className="space-y-6">
      <PageHeader
        title="Gmail Inbox"
        description="Browse synced mail, open a full reading pane, and inspect message metadata."
      />

      <div className="rounded-2xl border border-border bg-card/80 p-4 shadow-sm backdrop-blur-sm">
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 lg:flex-row lg:items-center">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              placeholder="Search subject, sender, recipient, or preview"
              className="h-11 w-full rounded-xl border border-border bg-background pl-10 pr-4 text-sm text-foreground outline-none transition-colors focus:border-primary"
            />
          </div>
          <div className="relative">
            <input
              value={exclude}
              onChange={(e) => setExclude(e.target.value)}
              placeholder="Exclude text"
              className="h-11 rounded-xl border border-border bg-background px-3 py-2 text-sm text-foreground outline-none transition-colors focus:border-primary"
            />
          </div>
          <button
            type="submit"
            className="inline-flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition hover:bg-primary/95"
          >
            <Filter className="h-4 w-4" />
            Filter
          </button>
          <button
            type="button"
            onClick={syncGmailInbox}
            disabled={syncing}
            className="inline-flex items-center justify-center gap-2 rounded-xl border border-border bg-background px-4 py-2.5 text-sm font-semibold text-foreground transition hover:bg-muted disabled:opacity-50"
          >
            <RefreshCw className={`h-4 w-4 ${syncing ? 'animate-spin' : ''}`} />
            Sync Inbox
          </button>
        </form>
      </div>

      <div className="overflow-hidden rounded-2xl border border-border bg-card shadow-sm">
        {loading ? (
          <div className="flex h-72 items-center justify-center">
            <div className="flex flex-col items-center gap-3 text-muted-foreground">
              <RefreshCw className="h-8 w-8 animate-spin text-primary" />
              <span className="text-sm">Loading messages</span>
            </div>
          </div>
        ) : error ? (
          <div className="flex h-72 flex-col items-center justify-center p-6 text-center">
            <AlertCircle className="mb-3 h-10 w-10 text-destructive" />
            <h4 className="text-lg font-semibold text-foreground">Inbox unavailable</h4>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">{error}</p>
          </div>
        ) : filteredMessages.length === 0 ? (
          <div className="flex h-72 flex-col items-center justify-center p-6 text-center">
            <Inbox className="mb-3 h-10 w-10 text-muted-foreground" />
            <h4 className="text-lg font-semibold text-foreground">No Gmail messages found</h4>
            <p className="mt-2 max-w-md text-sm text-muted-foreground">
              Connect Gmail, then press Sync Inbox to fetch the latest mail.
            </p>
          </div>
        ) : (
          <div className="grid gap-0 lg:grid-cols-[1.1fr_0.9fr]">
            <div className="divide-y divide-border">
              {filteredMessages.map((message) => (
                <button
                  key={message.id}
                  type="button"
                  onClick={() => setSelected(message)}
                  className={`w-full px-5 py-4 text-left transition hover:bg-muted/40 ${
                    selected?.id === message.id ? 'bg-muted/50' : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <div className={`mt-1 rounded-full p-2 ${message.unread ? 'bg-primary/10 text-primary' : 'bg-muted text-muted-foreground'}`}>
                      <Mail className="h-4 w-4" />
                    </div>
                    <div className="min-w-0 flex-1">
                      <div className="flex flex-wrap items-center gap-2">
                        <p className="truncate text-sm font-semibold text-foreground">
                          {message.subject || '(No Subject)'}
                        </p>
                        {message.unread && (
                          <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[11px] font-semibold text-primary">
                            Unread
                          </span>
                        )}
                        {message.attachments.length > 0 && (
                          <span className="inline-flex items-center gap-1 rounded-full bg-muted px-2 py-0.5 text-[11px] text-muted-foreground">
                            <Paperclip className="h-3 w-3" />
                            {message.attachments.length}
                          </span>
                        )}
                      </div>
                      <div className="mt-1 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                        <span className="inline-flex items-center gap-1">
                          <UserRound className="h-3.5 w-3.5" />
                          {message.sender_name}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <AtSign className="h-3.5 w-3.5" />
                          {message.sender_address}
                        </span>
                        <span className="inline-flex items-center gap-1">
                          <CalendarDays className="h-3.5 w-3.5" />
                          {new Date(message.created_at).toLocaleString()}
                        </span>
                      </div>
                      <p className="mt-2 line-clamp-2 text-sm text-muted-foreground">
                        {message.snippet || message.body}
                      </p>
                    </div>
                  </div>
                </button>
              ))}
            </div>

            <div className="border-t border-border bg-muted/20 p-5 lg:border-l lg:border-t-0">
              {selected ? (
                <div className="space-y-5">
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <Mail className="h-5 w-5 text-primary" />
                        <h3 className="truncate text-lg font-semibold text-foreground">
                          {selected.subject || '(No Subject)'}
                        </h3>
                      </div>
                      <p className="mt-2 text-sm text-muted-foreground">
                        {selected.sender_name} &lt;{selected.sender_address}&gt;
                      </p>
                    </div>
                    <button
                      type="button"
                      onClick={() => setSelected(null)}
                      className="rounded-lg p-2 text-muted-foreground transition hover:bg-background hover:text-foreground lg:hidden"
                    >
                      <X className="h-4 w-4" />
                    </button>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-2">
                    <div className="rounded-xl border border-border bg-background p-3">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">To</p>
                      <p className="mt-1 text-sm text-foreground">{selected.recipient_address || 'Unknown'}</p>
                    </div>
                    <div className="rounded-xl border border-border bg-background p-3">
                      <p className="text-[11px] uppercase tracking-wide text-muted-foreground">Received</p>
                      <p className="mt-1 text-sm text-foreground">{new Date(selected.created_at).toLocaleString()}</p>
                    </div>
                  </div>

                  <div className="flex flex-wrap gap-2">
                    {selected.labels.length > 0 ? (
                      selected.labels.map((label) => (
                        <span
                          key={label}
                          className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-1 text-xs text-foreground"
                        >
                          <Tags className="h-3 w-3 text-muted-foreground" />
                          {label}
                        </span>
                      ))
                    ) : (
                      <span className="inline-flex items-center gap-1 rounded-full border border-border bg-background px-2.5 py-1 text-xs text-muted-foreground">
                        <Tags className="h-3 w-3" />
                        No labels
                      </span>
                    )}
                  </div>

                  <div className="rounded-2xl border border-border bg-background p-4">
                    <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      <MessageSquareText className="h-4 w-4" />
                      Main Content
                    </div>
                    <div className="whitespace-pre-wrap text-sm leading-6 text-foreground">
                      {selected.body}
                    </div>
                  </div>

                  <div className="rounded-2xl border border-border bg-background p-4">
                    <div className="mb-3 flex items-center gap-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
                      <Paperclip className="h-4 w-4" />
                      Attachments
                    </div>
                    {selected.attachments.length > 0 ? (
                      <div className="space-y-2">
                        {selected.attachments.map((attachment) => (
                          <div key={attachment.id} className="flex items-center justify-between rounded-xl border border-border px-3 py-2">
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium text-foreground">{attachment.name}</p>
                              <p className="text-xs text-muted-foreground">
                                {attachment.size_bytes ? `${attachment.size_bytes} bytes` : 'Unknown size'}
                              </p>
                            </div>
                            <Paperclip className="h-4 w-4 shrink-0 text-muted-foreground" />
                          </div>
                        ))}
                      </div>
                    ) : (
                      <p className="text-sm text-muted-foreground">No attachments on this message.</p>
                    )}
                  </div>
                </div>
              ) : (
                <div className="flex h-full min-h-[24rem] items-center justify-center text-center text-muted-foreground">
                  <div>
                    <Eye className="mx-auto mb-3 h-10 w-10" />
                    <p className="text-sm font-medium text-foreground">Select a message</p>
                    <p className="mt-1 max-w-sm text-xs text-muted-foreground">
                      Open any email to inspect its full body, labels, and attachments here.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </PageTransition>
  );
}

export default GmailPage;
