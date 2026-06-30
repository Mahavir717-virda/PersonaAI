import { useState } from 'react';
import { Settings as SettingsIcon, Brain, Save } from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import { useAuthStore } from '@/store/auth.store';
import { useThemeStore } from '@/store/theme.store';
import { userService } from '@/services/user.service';
import { PageTransition } from '@/components/animations/PageTransition';

export function SettingsPage() {
  const { user, setUser } = useAuthStore();
  const { theme: storeTheme, setTheme } = useThemeStore();

  const [theme, setLocalTheme] = useState(user?.settings?.theme || storeTheme);
  const [language, setLanguage] = useState(user?.settings?.language || 'en');
  const [timezone, setTimezone] = useState(user?.settings?.timezone || 'UTC');
  const [aiPersonality, setAiPersonality] = useState(user?.settings?.ai_personality || 'professional');
  const [summaryLength, setSummaryLength] = useState(user?.settings?.preferred_summary_length || 'medium');
  const [memoryEnabled, setMemoryEnabled] = useState(user?.settings?.memory_enabled !== false);

  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const response = await userService.updateMe({
        theme,
        language,
        timezone,
      });
      setUser(response.data);
      // Sync global theme store
      setTheme(theme as 'dark' | 'light' | 'system');
      setMessage('Settings updated successfully.');
    } catch (err) {
      console.error(err);
      setMessage('Failed to update settings.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageTransition className="space-y-6 max-w-2xl">
      <PageHeader
        title="Settings"
        description="Configure your application interface preferences and AI assistant personality traits."
      />

      <form onSubmit={handleSave} className="space-y-6">
        {message && (
          <div className="p-3 rounded-lg text-sm border bg-green-500/10 border-green-500/20 text-green-400">
            {message}
          </div>
        )}

        {/* Global Settings */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <SettingsIcon className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-foreground">Preferences</h3>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">Theme</label>
              <select
                value={theme}
                onChange={(e) => setLocalTheme(e.target.value)}
                className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              >
                <option value="dark">Dark Theme</option>
                <option value="light">Light Theme</option>
                <option value="system">System Default</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">Language</label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              >
                <option value="en">English (US)</option>
                <option value="es">Español</option>
                <option value="de">Deutsch</option>
                <option value="fr">Français</option>
              </select>
            </div>

            <div className="space-y-2 sm:col-span-2">
              <label className="text-sm font-semibold text-foreground">Timezone</label>
              <select
                value={timezone}
                onChange={(e) => setTimezone(e.target.value)}
                className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              >
                <option value="UTC">UTC (Universal Time Coordinated)</option>
                <option value="America/New_York">EST (Eastern Standard Time)</option>
                <option value="Europe/London">GMT (Greenwich Mean Time)</option>
                <option value="Asia/Kolkata">IST (Indian Standard Time)</option>
              </select>
            </div>
          </div>
        </div>

        {/* AI Profile Settings */}
        <div className="rounded-xl border border-border bg-card p-6 space-y-4">
          <div className="flex items-center gap-2 border-b border-border pb-3">
            <Brain className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-foreground">AI Configuration</h3>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">AI Personality</label>
              <select
                value={aiPersonality}
                onChange={(e) => setAiPersonality(e.target.value)}
                className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              >
                <option value="professional">Professional / Concise</option>
                <option value="casual">Casual / Friendly</option>
                <option value="creative">Creative / Brainstormer</option>
              </select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-semibold text-foreground">Summary Length</label>
              <select
                value={summaryLength}
                onChange={(e) => setSummaryLength(e.target.value)}
                className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground outline-none focus:border-primary"
              >
                <option value="short">Short (Bullet Points)</option>
                <option value="medium">Medium (One Paragraph)</option>
                <option value="long">Detailed Summary</option>
              </select>
            </div>

            <div className="sm:col-span-2 flex items-center justify-between py-2">
              <div>
                <h4 className="text-sm font-semibold text-foreground">Enable AI Memory</h4>
                <p className="text-xs text-muted-foreground">Allows AI to retain context from previous session summaries.</p>
              </div>
              <input
                type="checkbox"
                checked={memoryEnabled}
                onChange={(e) => setMemoryEnabled(e.target.checked)}
                className="h-5 w-5 rounded border-border bg-background text-primary focus:ring-primary"
              />
            </div>
          </div>
        </div>

        <button
          type="submit"
          disabled={saving}
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-3 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 disabled:opacity-50"
        >
          <Save className="h-4 w-4" />
          {saving ? 'Saving...' : 'Save Settings'}
        </button>
      </form>
    </PageTransition>
  );
}
export default SettingsPage;
