import { useState } from 'react';
import { Search, Bell, Sun, Moon } from 'lucide-react';
import { useThemeStore } from '@/store/theme.store';
import { useNotificationStore } from '@/store/notification.store';
import { UserMenu } from './UserMenu';
import { cn } from '@/lib/utils';

export function Navbar() {
  const { theme, toggleTheme } = useThemeStore();
  const { unreadCount, notifications, markAllRead } = useNotificationStore();
  const [searchFocused, setSearchFocused] = useState(false);
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-border bg-card/80 px-6 backdrop-blur-xl">
      {/* Search */}
      <div className="relative flex-1 max-w-md">
        <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
        <input
          type="text"
          placeholder="Search messages, contacts, tasks..."
          className={cn(
            'h-9 w-full rounded-lg border bg-muted/50 pl-9 pr-4 text-sm text-foreground placeholder:text-muted-foreground outline-none transition-all',
            searchFocused
              ? 'border-primary ring-1 ring-primary/20'
              : 'border-transparent hover:border-border',
          )}
          onFocus={() => setSearchFocused(true)}
          onBlur={() => setSearchFocused(false)}
        />
        <kbd className="pointer-events-none absolute right-3 top-1/2 -translate-y-1/2 rounded border border-border px-1.5 py-0.5 text-[10px] text-muted-foreground">
          ⌘K
        </kbd>
      </div>

      {/* Actions */}
      <div className="flex items-center gap-1">
        {/* Notifications */}
        <div className="relative">
          <button
            onClick={() => setNotifOpen(!notifOpen)}
            className="relative rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
            aria-label="Notifications"
          >
            <Bell className="h-5 w-5" />
            {unreadCount > 0 && (
              <span className="absolute right-1 top-1 flex h-4 w-4 items-center justify-center rounded-full bg-primary text-[10px] font-bold text-primary-foreground">
                {unreadCount}
              </span>
            )}
          </button>

          {notifOpen && (
            <div className="absolute right-0 top-full mt-2 w-80 rounded-xl border border-border bg-card p-2 shadow-xl z-50 animate-fade-in">
              <div className="flex items-center justify-between px-3 py-2">
                <h3 className="text-sm font-semibold text-foreground">
                  Notifications
                </h3>
                {unreadCount > 0 && (
                  <button
                    onClick={() => markAllRead()}
                    className="text-xs text-primary hover:underline"
                  >
                    Mark all read
                  </button>
                )}
              </div>
              <div className="max-h-64 overflow-y-auto space-y-1">
                {notifications.length === 0 ? (
                  <p className="px-3 py-4 text-center text-sm text-muted-foreground">
                    No notifications
                  </p>
                ) : (
                  notifications.map((n) => (
                    <div
                      key={n.id}
                      className={cn(
                        'rounded-lg px-3 py-2 text-sm transition-colors hover:bg-muted',
                        !n.read && 'bg-primary/5',
                      )}
                    >
                      <p className="font-medium text-foreground">{n.title}</p>
                      <p className="text-xs text-muted-foreground line-clamp-2">
                        {n.message}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </div>

        {/* Theme Toggle */}
        <button
          onClick={toggleTheme}
          className="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground"
          aria-label="Toggle theme"
        >
          {theme === 'dark' ? (
            <Sun className="h-5 w-5" />
          ) : (
            <Moon className="h-5 w-5" />
          )}
        </button>

        {/* User Menu */}
        <UserMenu />
      </div>
    </header>
  );
}
