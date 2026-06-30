import { useState, useEffect } from 'react';
import {
  Search as SearchIcon,
  RefreshCw,
  Mail,
  MessageCircle,
  Globe,
  Filter,
  ChevronLeft,
  ChevronRight,
  Eye,
  FileText,
  Calendar,
} from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import { PageTransition } from '@/components/animations/PageTransition';
import apiClient from '@/services/api.client';

interface CommunicationItem {
  id: string;
  platform: string;
  platform_message_id: string;
  subject: string | null;
  body: string;
  html_body: string | null;
  status: string;
  importance: string;
  created_at: string;
  sender_name: string;
  sender_address: string;
  receivers: string[];
  attachments: Array<{
    id: string;
    name: string;
    content_type: string | null;
    url: string | null;
    size_bytes: number | null;
  }>;
  metadata: Record<string, any>;
}

const iconMap: Record<string, any> = {
  gmail: Mail,
  whatsapp: MessageCircle,
};

const badgeColor: Record<string, string> = {
  gmail: 'bg-red-500/10 text-red-400',
  whatsapp: 'bg-green-500/10 text-green-400',
};

export function CommunicationsPage() {
  const [communications, setCommunications] = useState<CommunicationItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchQuery, setSearchQuery] = useState('');
  const [platformFilter, setPlatformFilter] = useState('');
  const [excludeQuery, setExcludeQuery] = useState('');
  const [selectedMsg, setSelectedMsg] = useState<CommunicationItem | null>(null);

  // Pagination states
  const [page, setPage] = useState(1);
  const limit = 15;

  const fetchCommunications = async () => {
    setLoading(true);
    try {
      let url = '/api/v1/communications';
      const params: Record<string, any> = {
        limit,
        offset: (page - 1) * limit,
      };

      if (platformFilter) {
        params.platform = platformFilter;
      }

      if (excludeQuery) {
        params.exclude_query = excludeQuery;
      }

      if (searchQuery) {
        url = '/api/v1/communications/search';
        params.query = searchQuery;
      }

      const response = await apiClient.get(url, { params });
      setCommunications(response.data.data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCommunications();
  }, [page, platformFilter, excludeQuery]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setPage(1);
    fetchCommunications();
  };

  return (
    <PageTransition className="space-y-6">
      <PageHeader
        title="Communication Explorer"
        description="Browse, search, and inspect all normalized messages indexed across your connected accounts."
      />

      {/* Search & Filter Controls */}
      <div className="rounded-xl border border-border bg-card p-4">
        <form onSubmit={handleSearchSubmit} className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <input
              type="text"
              placeholder="Search by sender, subject, keywords..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="h-10 w-full rounded-lg border border-border bg-background pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary"
            />
          </div>

          <div className="flex flex-wrap gap-2">
            <div className="relative">
              <select
                value={platformFilter}
                onChange={(e) => {
                  setPage(1);
                  setPlatformFilter(e.target.value);
                }}
                className="h-10 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              >
                <option value="">All Platforms</option>
                <option value="gmail">Gmail</option>
                <option value="whatsapp">WhatsApp</option>
              </select>
            </div>

            <input
              type="text"
              value={excludeQuery}
              onChange={(e) => setExcludeQuery(e.target.value)}
              placeholder="Exclude pattern"
              className="h-10 rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary"
            />

            <button
              type="submit"
              className="inline-flex items-center gap-1.5 rounded-lg bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/95"
            >
              <Filter className="h-4 w-4" />
              Filter
            </button>
          </div>
        </form>
      </div>

      {/* Explorer Table */}
      <div className="rounded-xl border border-border bg-card overflow-hidden">
        {loading ? (
          <div className="flex h-64 items-center justify-center">
            <RefreshCw className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : communications.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-64 text-center p-6">
            <Globe className="h-8 w-8 text-muted-foreground mb-3" />
            <h4 className="font-semibold text-foreground">No messages found</h4>
            <p className="text-xs text-muted-foreground max-w-xs mt-1">
              Verify your connectors are active or adjust your search filters.
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-sm">
              <thead>
                <tr className="border-b border-border bg-muted/20 text-muted-foreground">
                  <th className="px-6 py-3 font-semibold">Platform</th>
                  <th className="px-6 py-3 font-semibold">Sender</th>
                  <th className="px-6 py-3 font-semibold">Subject / Preview</th>
                  <th className="px-6 py-3 font-semibold">Received</th>
                  <th className="px-6 py-3 font-semibold">Priority</th>
                  <th className="px-6 py-3 font-semibold text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border">
                {communications.map((item) => {
                  const PlatformIcon = iconMap[item.platform] || Globe;
                  return (
                    <tr key={item.id} className="hover:bg-muted/30 transition-colors">
                      <td className="px-6 py-4">
                        <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${badgeColor[item.platform] || 'bg-muted'}`}>
                          <PlatformIcon className="h-3.5 w-3.5" />
                          <span className="capitalize">{item.platform}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 font-medium text-foreground">
                        <div>
                          <p>{item.sender_name}</p>
                          <p className="text-xs text-muted-foreground">{item.sender_address}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="max-w-md">
                          <p className="font-semibold text-foreground truncate">{item.subject || '(No Subject)'}</p>
                          <p className="text-xs text-muted-foreground truncate">{item.body}</p>
                        </div>
                      </td>
                      <td className="px-6 py-4 text-muted-foreground">
                        {new Date(item.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4">
                        <span className={`inline-flex rounded px-1.5 py-0.5 text-xs font-medium capitalize ${item.importance === 'high' ? 'bg-destructive/10 text-destructive' : 'bg-muted text-muted-foreground'
                          }`}>
                          {item.importance}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-right">
                        <button
                          onClick={() => setSelectedMsg(item)}
                          className="rounded p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
                          title="Open Message"
                        >
                          <Eye className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Pagination */}
      {communications.length > 0 && (
        <div className="flex items-center justify-between">
          <p className="text-xs text-muted-foreground">
            Showing Page {page}
          </p>
          <div className="flex gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="inline-flex rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground transition-all hover:bg-muted disabled:opacity-50"
            >
              <ChevronLeft className="h-4 w-4" />
            </button>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={communications.length < limit}
              className="inline-flex rounded-lg border border-border bg-card px-3 py-1.5 text-xs font-semibold text-foreground transition-all hover:bg-muted disabled:opacity-50"
            >
              <ChevronRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* Message Inspector Modal */}
      {selectedMsg && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm p-4">
          <div className="w-full max-w-2xl rounded-xl border border-border bg-card p-6 shadow-2xl animate-fade-in flex flex-col max-h-[85vh]">
            <div className="flex justify-between items-start border-b border-border pb-4 mb-4">
              <div>
                <h3 className="text-lg font-bold text-foreground">
                  {selectedMsg.subject || '(No Subject)'}
                </h3>
                <div className="flex items-center gap-2 mt-1">
                  <span className={`inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${badgeColor[selectedMsg.platform] || 'bg-muted'}`}>
                    <span className="capitalize">{selectedMsg.platform}</span>
                  </span>
                  <span className="text-xs text-muted-foreground flex items-center gap-1">
                    <Calendar className="h-3 w-3" />
                    {new Date(selectedMsg.created_at).toLocaleString()}
                  </span>
                </div>
              </div>
              <button
                onClick={() => setSelectedMsg(null)}
                className="rounded-lg p-1.5 text-muted-foreground hover:bg-muted hover:text-foreground"
              >
                Close
              </button>
            </div>

            <div className="flex-1 overflow-y-auto space-y-4 pr-2">
              {/* Sender Info */}
              <div className="rounded-lg bg-muted/30 p-3 text-sm">
                <p className="text-xs text-muted-foreground">From</p>
                <p className="font-semibold text-foreground">
                  {selectedMsg.sender_name} <span className="font-normal text-muted-foreground">(&lt;{selectedMsg.sender_address}&gt;)</span>
                </p>
              </div>

              {/* Message Body */}
              <div className="text-sm text-foreground whitespace-pre-wrap leading-relaxed border border-border/50 rounded-lg p-4">
                {selectedMsg.body}
              </div>

              {/* Attachments */}
              {selectedMsg.attachments.length > 0 && (
                <div className="space-y-2">
                  <h5 className="text-xs font-semibold text-foreground">Attachments ({selectedMsg.attachments.length})</h5>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {selectedMsg.attachments.map((att) => (
                      <div key={att.id} className="flex items-center gap-2 rounded-lg border border-border p-2.5 text-xs bg-muted/20">
                        <FileText className="h-4 w-4 text-primary" />
                        <div className="flex-1 min-w-0">
                          <p className="font-medium text-foreground truncate">{att.name}</p>
                          <p className="text-muted-foreground">{att.size_bytes ? `${(att.size_bytes / 1024).toFixed(1)} KB` : ''}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </PageTransition>
  );
}
export default CommunicationsPage;
