import { motion, type HTMLMotionProps } from 'framer-motion';
import type { ReactNode } from 'react';

interface PageTransitionProps extends HTMLMotionProps<'div'> {
  children: ReactNode;
}

export function PageTransition({ children, ...props }: PageTransitionProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0, y: -8 }}
      transition={{ duration: 0.3, ease: 'easeInOut' }}
      {...props}
    >
      {children}
    </motion.div>
  );
}
