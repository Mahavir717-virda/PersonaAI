import { cn } from '@/lib/utils';

interface SkeletonCardProps {
  className?: string;
}

export function SkeletonCard({ className }: SkeletonCardProps) {
  return (
    <div
      className={cn(
        'rounded-xl border border-border bg-card p-6 animate-pulse',
        className,
      )}
    >
      <div className="mb-4 flex items-center justify-between">
        <div className="h-4 w-24 rounded bg-muted" />
        <div className="h-8 w-8 rounded-lg bg-muted" />
      </div>
      <div className="h-8 w-20 rounded bg-muted mb-2" />
      <div className="h-3 w-32 rounded bg-muted" />
    </div>
  );
}
