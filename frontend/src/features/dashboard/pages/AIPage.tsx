import React, { useState } from 'react';
import { PageHeader } from '@/components/common/PageHeader';
import { Sparkles, Brain, ListChecks, Calendar, Users, Briefcase, FileText } from 'lucide-react';
import apiClient from '@/services/api.client';

interface SummaryDetail {
  tldr: string;
  summary: string;
  key_points: string[];
  decisions: string[];
  action_items: string[];
  deadlines: string[];
  people: string[];
  organizations: string[];
  projects: string[];
  meetings: string[];
  risks: string[];
  follow_ups: string[];
  questions: string[];
  topics: string[];
}

export function AIPage() {
  const [threadText, setThreadText] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [summary, setSummary] = useState<SummaryDetail | null>(null);

  const handleSummarize = async () => {
    if (!threadText.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const resp = await apiClient.post('/api/v1/brain/chat', {
        source: 'gmail',
        mode: 'summarize',
        thread: threadText
      });
      if (resp.data?.summary) {
        setSummary(resp.data.summary);
      } else {
        setError('No summary payload returned from backend.');
      }
    } catch (err: any) {
      setError(err.response?.data?.details?.detail || err.message || 'Failed to connect to the summary model.');
    } finally {
      setLoading(false);
    }
  };

  const renderSection = (title: string, items: string[], Icon: any, color: string) => {
    if (!items || items.length === 0) return null;
    return (
      <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
        <div className="flex items-center gap-2 border-b border-border pb-3 mb-3">
          <Icon className={`h-5 w-5 ${color}`} />
          <h3 className="font-semibold text-foreground">{title}</h3>
        </div>
        <ul className="list-disc pl-5 space-y-1 text-sm text-muted-foreground">
          {items.map((item, idx) => (
            <li key={idx}>{item}</li>
          ))}
        </ul>
      </div>
    );
  };

  return (
    <div className="space-y-6 max-w-6xl mx-auto">
      <PageHeader
        title="AI Brain Playground"
        description="Paste email threads to run the fine-tuned Local Llama 3.2 1B Summary Model and extract structured workflows."
      />

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Side: Input Panel */}
        <div className="md:col-span-1 space-y-4">
          <div className="rounded-xl border border-border bg-card p-5 shadow-sm">
            <h2 className="font-semibold text-foreground flex items-center gap-2 mb-3">
              <Brain className="h-5 w-5 text-primary" />
              Conversation Thread
            </h2>
            <textarea
              className="w-full h-80 rounded-lg border border-input bg-background p-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              placeholder="Paste email thread here..."
              value={threadText}
              onChange={(e) => setThreadText(e.target.value)}
            />
            <button
              onClick={handleSummarize}
              disabled={loading || !threadText.trim()}
              className="w-full mt-4 flex items-center justify-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all shadow-sm"
            >
              <Sparkles className="h-4 w-4" />
              {loading ? 'Analyzing with Llama...' : 'Analyze Thread'}
            </button>
            {error && (
              <div className="mt-3 text-xs text-destructive bg-destructive/10 p-2.5 rounded-lg border border-destructive/20">
                {error}
              </div>
            )}
          </div>
        </div>

        {/* Right Side: Structured Summary Results */}
        <div className="md:col-span-2 space-y-6">
          {summary ? (
            <div className="space-y-6">
              {/* TLDR & Summary Card */}
              <div className="rounded-xl border border-border bg-card p-6 shadow-sm space-y-4">
                {summary.tldr && (
                  <div className="bg-primary/5 border border-primary/20 p-4 rounded-xl">
                    <span className="text-xs font-bold uppercase tracking-wider text-primary">TLDR</span>
                    <p className="mt-1 text-base font-semibold text-foreground">{summary.tldr}</p>
                  </div>
                )}
                {summary.summary && (
                  <div className="space-y-2">
                    <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">Full Summary</span>
                    <p className="text-sm text-muted-foreground leading-relaxed">{summary.summary}</p>
                  </div>
                )}
              </div>

              {/* Grid of details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                {renderSection("Action Items", summary.action_items, ListChecks, "text-green-500")}
                {renderSection("Deadlines", summary.deadlines, Calendar, "text-red-500")}
                {renderSection("People Involved", summary.people, Users, "text-blue-500")}
                {renderSection("Projects", summary.projects, Briefcase, "text-purple-500")}
                {renderSection("Meetings Scheduled", summary.meetings, Calendar, "text-amber-500")}
                {renderSection("Key Points", summary.key_points, FileText, "text-cyan-500")}
                {renderSection("Decisions Made", summary.decisions, ListChecks, "text-emerald-500")}
                {renderSection("Risks Identified", summary.risks, Sparkles, "text-rose-500")}
                {renderSection("Follow-ups", summary.follow_ups, FileText, "text-indigo-500")}
                {renderSection("Questions", summary.questions, Sparkles, "text-orange-500")}
              </div>
            </div>
          ) : (
            <div className="rounded-xl border border-border border-dashed bg-card/50 p-12 text-center text-muted-foreground h-full flex flex-col justify-center items-center">
              <Brain className="h-12 w-12 text-muted-foreground/30 mb-3" />
              <p className="text-base font-semibold">No active analysis</p>
              <p className="text-sm text-muted-foreground max-w-sm mt-1">
                Paste an email thread on the left and click "Analyze Thread" to view deconstructed semantic workflows.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
