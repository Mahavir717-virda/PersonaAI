import { Link } from 'react-router-dom';
import { ShieldX, ArrowLeft } from 'lucide-react';
import { FadeIn } from '@/components/animations/FadeIn';

export function UnauthorizedPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <FadeIn className="text-center">
        <div className="mx-auto mb-6 inline-flex rounded-full bg-destructive/10 p-6">
          <ShieldX className="h-12 w-12 text-destructive" />
        </div>
        <h1 className="mb-2 text-3xl font-bold text-foreground">
          Access Denied
        </h1>
        <p className="mb-8 max-w-md text-muted-foreground">
          You don&apos;t have permission to access this page. Please sign in
          with an authorized account or contact your administrator.
        </p>
        <Link
          to="/login"
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Sign In
        </Link>
      </FadeIn>
    </div>
  );
}
