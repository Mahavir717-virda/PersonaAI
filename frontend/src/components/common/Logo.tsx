import { Sparkles } from 'lucide-react';
import { cn } from '@/lib/utils';

interface LogoProps {
  className?: string;
  size?: 'sm' | 'md' | 'lg';
  showText?: boolean;
}

const sizes = {
  sm: 'h-6 w-6',
  md: 'h-8 w-8',
  lg: 'h-10 w-10',
};

const textSizes = {
  sm: 'text-lg',
  md: 'text-xl',
  lg: 'text-2xl',
};

export function Logo({ className, size = 'md', showText = true }: LogoProps) {
  return (
    <div className={cn('flex items-center gap-2', className)}>
      <div
        className={cn(
          'flex items-center justify-center rounded-lg bg-gradient-to-br from-primary to-accent',
          sizes[size],
        )}
      >
        <Sparkles className="h-[60%] w-[60%] text-white" />
      </div>
      {showText && (
        <span
          className={cn(
            'font-bold tracking-tight bg-gradient-to-r from-primary to-accent bg-clip-text text-transparent',
            textSizes[size],
          )}
        >
          PersonaAI
        </span>
      )}
    </div>
  );
}
