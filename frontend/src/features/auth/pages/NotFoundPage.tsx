import { Link } from 'react-router-dom';
import { Ghost, ArrowLeft } from 'lucide-react';
import { FadeIn } from '@/components/animations/FadeIn';

export function NotFoundPage() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-background px-4">
      <FadeIn className="text-center">
        <div className="mx-auto mb-6 inline-flex rounded-full bg-muted p-6">
          <Ghost className="h-12 w-12 text-muted-foreground" />
        </div>
        <h1 className="mb-2 text-6xl font-bold text-foreground">404</h1>
        <p className="mb-2 text-xl font-semibold text-foreground">
          Page Not Found
        </p>
        <p className="mb-8 max-w-md text-muted-foreground">
          The page you&apos;re looking for doesn&apos;t exist or has been moved.
        </p>
        <Link
          to="/"
          className="inline-flex items-center gap-2 rounded-xl bg-primary px-6 py-3 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90"
        >
          <ArrowLeft className="h-4 w-4" />
          Back to Home
        </Link>
      </FadeIn>
    </div>
  );
}
