import { useState, useEffect, useCallback } from 'react';
import { Navigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Sparkles, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { Logo } from '@/components/common/Logo';
import { FloatingParticles } from '@/components/animations/FloatingParticles';
import { FadeIn } from '@/components/animations/FadeIn';
import { useAuthStore } from '@/store/auth.store';
import { authService } from '@/services/auth.service';
import { userService } from '@/services/user.service';

declare global {
  interface Window {
    google?: any;
  }
}

export function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated, login, setTokens } = useAuthStore();
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID;
  const googleClientIdConfigured = Boolean(
    clientId && clientId !== 'VITE_GOOGLE_CLIENT_ID' && clientId.trim(),
  );

  const handleCredentialResponse = useCallback(async (response: any) => {
    setLoading(true);
    setError(null);
    try {
      const tokenResponse = await authService.googleLogin(response.credential);
      const tokens = tokenResponse.data;
      setTokens(tokens);

      const userResponse = await userService.getMe();
      login(userResponse.data, tokens);
    } catch (err) {
      setError(
        'Authentication failed. Please ensure the backend is running and Google OAuth is configured.',
      );
      console.error('Login error:', err);
    } finally {
      setLoading(false);
    }
  }, [login, setTokens]);

  useEffect(() => {
    const initGsi = () => {
      if (!googleClientIdConfigured) {
        setError(
          'Google sign-in is not configured yet. Set VITE_GOOGLE_CLIENT_ID in frontend/.env and add http://localhost:3000 to Authorized JavaScript origins in Google Cloud Console.',
        );
        return;
      }

      if (window.google?.accounts?.id) {
        window.google.accounts.id.initialize({
          client_id: clientId,
          callback: handleCredentialResponse,
          auto_select: false,
          cancel_on_tap_outside: false,
        });
        window.google.accounts.id.renderButton(
          document.getElementById('google-signin-btn-container'),
          { theme: 'outline', size: 'large', width: '100%' },
        );
      } else {
        setTimeout(initGsi, 100);
      }
    };

    initGsi();
  }, [clientId, googleClientIdConfigured, handleCredentialResponse]);

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-background">
      <FloatingParticles />

      <FadeIn className="relative z-10 w-full max-w-md px-6">
        <div className="rounded-2xl border border-border bg-card/80 p-8 shadow-2xl shadow-primary/5 backdrop-blur-xl">
          {/* Back link */}
          <Link
            to="/"
            className="mb-6 inline-flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
          >
            <ArrowLeft className="h-4 w-4" />
            Back to home
          </Link>

          {/* Header */}
          <div className="mb-8 text-center">
            <div className="mb-4 flex justify-center">
              <Logo size="lg" />
            </div>
            <h1 className="text-2xl font-bold text-foreground">Welcome back</h1>
            <p className="mt-2 text-sm text-muted-foreground">
              Sign in to your AI communication platform
            </p>
          </div>

          {/* Error */}
          {error && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="mb-6 rounded-lg border border-destructive/20 bg-destructive/5 p-3 text-sm text-destructive"
            >
              {error}
            </motion.div>
          )}

          {/* Google Login Container */}
          <div className="flex justify-center min-h-[50px] mb-4">
            {loading ? (
              <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
            ) : (
              <div id="google-signin-btn-container" className="w-full flex justify-center" />
            )}
          </div>

          {/* Divider */}
          <div className="my-6 flex items-center gap-4">
            <div className="h-px flex-1 bg-border" />
            <span className="text-xs text-muted-foreground">
              Secure authentication
            </span>
            <div className="h-px flex-1 bg-border" />
          </div>

          {/* Info */}
          <div className="space-y-3">
            {[
              'End-to-end encrypted communication',
              'OAuth 2.0 with JWT token security',
              'No passwords stored on our servers',
            ].map((item) => (
              <div key={item} className="flex items-center gap-2 text-xs text-muted-foreground">
                <Sparkles className="h-3 w-3 text-primary" />
                {item}
              </div>
            ))}
          </div>
        </div>

        <p className="mt-6 text-center text-xs text-muted-foreground">
          By signing in, you agree to our Terms of Service and Privacy Policy.
        </p>
      </FadeIn>
    </div>
  );
}
export default LoginPage;
