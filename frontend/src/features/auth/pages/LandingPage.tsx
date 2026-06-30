import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  ArrowRight,
  Mail,
  MessageCircle,
  Sparkles,
  Shield,
  Zap,
  Brain,
} from 'lucide-react';
import { Logo } from '@/components/common/Logo';
import { FloatingParticles } from '@/components/animations/FloatingParticles';
import { FadeIn } from '@/components/animations/FadeIn';

const features = [
  {
    icon: Sparkles,
    title: 'AI-Powered Summaries',
    description:
      'Get intelligent digests of your communications across all platforms.',
  },
  {
    icon: Mail,
    title: 'Gmail Integration',
    description:
      'Connect your Gmail and let AI organize, prioritize, and summarize your inbox.',
  },
  {
    icon: MessageCircle,
    title: 'WhatsApp Sync',
    description:
      'Bring your WhatsApp conversations into one unified communication hub.',
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description:
      'OAuth 2.0, JWT tokens, encrypted data, and audit logging built in.',
  },
  {
    icon: Zap,
    title: 'Real-time Processing',
    description:
      'Messages are processed and analyzed in real-time as they arrive.',
  },
  {
    icon: Brain,
    title: 'Adaptive AI',
    description:
      'The more you use it, the better it understands your communication style.',
  },
];

export function LandingPage() {
  return (
    <div className="relative min-h-screen overflow-hidden bg-background">
      <FloatingParticles />

      {/* Navbar */}
      <nav className="relative z-10 flex items-center justify-between px-6 py-4 lg:px-12">
        <Logo size="lg" />
        <div className="flex items-center gap-4">
          <Link
            to="/login"
            className="rounded-lg px-4 py-2 text-sm font-medium text-muted-foreground transition-colors hover:text-foreground"
          >
            Sign In
          </Link>
          <Link
            to="/login"
            className="rounded-xl bg-primary px-5 py-2.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl hover:shadow-primary/30"
          >
            Get Started
          </Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="relative z-10 mx-auto max-w-5xl px-6 pt-20 pb-32 text-center lg:pt-32">
        <FadeIn>
          <div className="mb-6 inline-flex items-center gap-2 rounded-full border border-border bg-card/50 px-4 py-1.5 text-sm text-muted-foreground backdrop-blur-sm">
            <Sparkles className="h-4 w-4 text-primary" />
            Your AI Communication Operating System
          </div>
        </FadeIn>

        <FadeIn delay={0.1}>
          <h1 className="mx-auto max-w-4xl text-5xl font-bold leading-tight tracking-tight text-foreground lg:text-7xl">
            One platform for{' '}
            <span className="bg-gradient-to-r from-primary via-accent to-primary bg-clip-text text-transparent">
              all your
            </span>{' '}
            communications
          </h1>
        </FadeIn>

        <FadeIn delay={0.2}>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-muted-foreground">
            PersonaAI connects your Gmail, WhatsApp, and Slack — then uses AI to
            summarize, prioritize, and help you respond faster. Stay on top of
            every conversation, effortlessly.
          </p>
        </FadeIn>

        <FadeIn delay={0.3}>
          <div className="mt-10 flex flex-col items-center justify-center gap-4 sm:flex-row">
            <Link
              to="/login"
              className="group inline-flex items-center gap-2 rounded-xl bg-primary px-8 py-3.5 text-sm font-semibold text-primary-foreground shadow-lg shadow-primary/25 transition-all hover:bg-primary/90 hover:shadow-xl hover:shadow-primary/30"
            >
              Start Free
              <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-1" />
            </Link>
            <a
              href="#features"
              className="inline-flex items-center gap-2 rounded-xl border border-border bg-card/50 px-8 py-3.5 text-sm font-semibold text-foreground backdrop-blur-sm transition-all hover:bg-card"
            >
              Learn More
            </a>
          </div>
        </FadeIn>

        {/* Dashboard Preview */}
        <FadeIn delay={0.4}>
          <div className="mt-20 overflow-hidden rounded-2xl border border-border bg-card/50 p-1 shadow-2xl shadow-primary/5 backdrop-blur-xl">
            <div className="rounded-xl bg-gradient-to-br from-card via-card to-muted/30 p-8">
              <div className="grid grid-cols-3 gap-4">
                {[
                  { label: 'Total Messages', value: '2,847', change: '+12%' },
                  { label: 'AI Summaries', value: '156', change: '+24%' },
                  { label: 'Time Saved', value: '48h', change: '+18%' },
                ].map((stat) => (
                  <div
                    key={stat.label}
                    className="rounded-xl border border-border bg-background/50 p-4 text-left"
                  >
                    <p className="text-xs text-muted-foreground">{stat.label}</p>
                    <p className="mt-1 text-2xl font-bold text-foreground">
                      {stat.value}
                    </p>
                    <p className="mt-1 text-xs text-success">{stat.change}</p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </FadeIn>
      </section>

      {/* Features */}
      <section id="features" className="relative z-10 mx-auto max-w-6xl px-6 pb-32">
        <FadeIn>
          <h2 className="text-center text-3xl font-bold text-foreground lg:text-4xl">
            Everything you need to{' '}
            <span className="text-primary">communicate smarter</span>
          </h2>
          <p className="mx-auto mt-4 max-w-2xl text-center text-muted-foreground">
            Powerful features designed for teams and individuals who value
            clarity and speed.
          </p>
        </FadeIn>

        <div className="mt-16 grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, i) => (
            <FadeIn key={feature.title} delay={0.1 * i}>
              <motion.div
                whileHover={{ y: -4, transition: { duration: 0.2 } }}
                className="group rounded-2xl border border-border bg-card/50 p-6 backdrop-blur-sm transition-all hover:border-primary/20 hover:shadow-lg hover:shadow-primary/5"
              >
                <div className="mb-4 inline-flex rounded-xl bg-primary/10 p-3">
                  <feature.icon className="h-6 w-6 text-primary" />
                </div>
                <h3 className="mb-2 text-lg font-semibold text-foreground">
                  {feature.title}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {feature.description}
                </p>
              </motion.div>
            </FadeIn>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="relative z-10 border-t border-border bg-card/30 px-6 py-8 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <Logo size="sm" />
          <p className="text-sm text-muted-foreground">
            © {new Date().getFullYear()} PersonaAI. All rights reserved.
          </p>
        </div>
      </footer>
    </div>
  );
}
