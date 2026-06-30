import { useState } from 'react';
import { User as UserIcon, Mail, Shield, Save } from 'lucide-react';
import { PageHeader } from '@/components/common/PageHeader';
import { useAuthStore } from '@/store/auth.store';
import { userService } from '@/services/user.service';
import { PageTransition } from '@/components/animations/PageTransition';

export function ProfilePage() {
  const { user, setUser } = useAuthStore();
  const [fullName, setFullName] = useState(user?.profile?.full_name || '');
  const [avatarUrl, setAvatarUrl] = useState(user?.profile?.avatar_url || '');
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setMessage('');
    try {
      const response = await userService.updateMe({
        full_name: fullName,
        avatar_url: avatarUrl || undefined,
      });
      setUser(response.data);
      setMessage('Profile updated successfully.');
    } catch (err) {
      console.error(err);
      setMessage('Failed to update profile.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <PageTransition className="space-y-6 max-w-2xl">
      <PageHeader
        title="Profile Settings"
        description="Manage your account profile details and avatar settings."
      />

      <div className="rounded-xl border border-border bg-card p-6">
        <form onSubmit={handleSave} className="space-y-4">
          {message && (
            <div className={`p-3 rounded-lg text-sm border ${message.includes('success') ? 'bg-green-500/10 border-green-500/20 text-green-400' : 'bg-destructive/10 border-destructive/20 text-destructive'}`}>
              {message}
            </div>
          )}

          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">Email Address</label>
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2 text-sm text-muted-foreground">
              <Mail className="h-4 w-4" />
              <span>{user?.email}</span>
            </div>
            <p className="text-xs text-muted-foreground">Your account email cannot be changed.</p>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">Full Name</label>
            <div className="relative">
              <UserIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <input
                type="text"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                placeholder="John Doe"
                className="h-10 w-full rounded-lg border border-border bg-background pl-10 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary"
              />
            </div>
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">Avatar Image URL</label>
            <input
              type="url"
              value={avatarUrl}
              onChange={(e) => setAvatarUrl(e.target.value)}
              placeholder="https://example.com/avatar.jpg"
              className="h-10 w-full rounded-lg border border-border bg-background px-3 py-2 text-sm text-foreground placeholder:text-muted-foreground outline-none focus:border-primary"
            />
          </div>

          <div className="space-y-2">
            <label className="text-sm font-semibold text-foreground">Security Role</label>
            <div className="flex items-center gap-2 rounded-lg border border-border bg-muted/50 px-3 py-2 text-sm text-muted-foreground">
              <Shield className="h-4 w-4" />
              <span className="capitalize">{user?.role}</span>
            </div>
          </div>

          <button
            type="submit"
            disabled={saving}
            className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 disabled:opacity-50"
          >
            <Save className="h-4 w-4" />
            {saving ? 'Saving...' : 'Save Profile'}
          </button>
        </form>
      </div>
    </PageTransition>
  );
}
export default ProfilePage;
