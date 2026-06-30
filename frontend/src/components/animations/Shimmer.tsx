import { cn } from '@/lib/utils';

interface ShimmerProps {
  className?: string;
}

export function Shimmer({ className }: ShimmerProps) {
  return (
    <div
      className={cn(
        'animate-shimmer rounded-lg bg-gradient-to-r from-transparent via-white/5 to-transparent bg-[length:200%_100%]',
        className,
      )}
    />
  );
}
