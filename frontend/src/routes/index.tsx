import { createBrowserRouter } from 'react-router-dom';
import { AppLayout } from '@/components/layout/AppLayout';
import { ProtectedRoute } from './ProtectedRoute';
import { LandingPage } from '@/features/auth/pages/LandingPage';
import { LoginPage } from '@/features/auth/pages/LoginPage';
import { UnauthorizedPage } from '@/features/auth/pages/UnauthorizedPage';
import { NotFoundPage } from '@/features/auth/pages/NotFoundPage';
import { DashboardPage } from '@/features/dashboard/pages/DashboardPage';
import { ProfilePage } from '@/features/profile/pages/ProfilePage';
import { SettingsPage } from '@/features/settings/pages/SettingsPage';
import { ConnectorsPage } from '@/features/connectors/pages/ConnectorsPage';
import { ConnectorDetailPage } from '@/features/connectors/pages/ConnectorDetailPage';
import { CommunicationsPage } from '@/features/communications/pages/CommunicationsPage';
import { GmailPage } from '@/features/gmail/pages/GmailPage';
import { AIPage } from '@/features/dashboard/pages/AIPage';
import { EmptyState as BaseEmptyState } from '@/components/common/EmptyState';
import { PageHeader } from '@/components/common/PageHeader';
import { MessageCircle, Sparkles, CheckSquare, Search } from 'lucide-react';

// Common placeholder helper for undeveloped routes
function FeaturePlaceholder({ title, description, icon: Icon }: { title: string; description: string; icon: any }) {
  return (
    <div className="space-y-6">
      <PageHeader title={title} description={`Manage your ${title.toLowerCase()} configurations.`} />
      <div className="rounded-xl border border-border bg-card p-6">
        <BaseEmptyState
          icon={<Icon className="h-8 w-8 text-primary" />}
          title={`${title} Module`}
          description={description}
          action={
            <button
              onClick={() => alert(`${title} connector initialization is coming in Phase 2.`)}
              className="inline-flex items-center gap-2 rounded-xl bg-primary px-4 py-2.5 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90"
            >
              Configure {title}
            </button>
          }
        />
      </div>
    </div>
  );
}

export const router = createBrowserRouter([
  // Public Routes
  {
    path: '/',
    element: <LandingPage />,
  },
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/unauthorized',
    element: <UnauthorizedPage />,
  },

  // Protected Dashboard Routes
  {
    path: '/dashboard',
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          {
            index: true,
            element: <DashboardPage />,
          },
          {
            path: 'communications',
            element: <CommunicationsPage />,
          },
          {
            path: 'ai',
            element: <AIPage />,
          },
          {
            path: 'gmail',
            element: <GmailPage />,
          },
          {
            path: 'whatsapp',
            element: (
              <FeaturePlaceholder
                title="WhatsApp Messages"
                description="Access WhatsApp logs, monitor status, and review automated AI chat responses."
                icon={MessageCircle}
              />
            ),
          },
          {
            path: 'connectors',
            element: <ConnectorsPage />,
          },
          {
            path: 'connectors/:platform',
            element: <ConnectorDetailPage />,
          },
          {
            path: 'tasks',
            element: (
              <FeaturePlaceholder
                title="Pending Tasks"
                description="Review tasks extracted from your emails and messages by our NLP engine."
                icon={CheckSquare}
              />
            ),
          },
          {
            path: 'search',
            element: (
              <FeaturePlaceholder
                title="Vector Search"
                description="Perform semantic search queries across all message vectors in your workspace."
                icon={Search}
              />
            ),
          },
          {
            path: 'profile',
            element: <ProfilePage />,
          },
          {
            path: 'settings',
            element: <SettingsPage />,
          },
        ],
      },
    ],
  },

  // 404 Route
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
