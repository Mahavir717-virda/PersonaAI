import { useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/auth.store';
import { authService } from '@/services/auth.service';
import { userService } from '@/services/user.service';

export function useAuth() {
  const { login, logout: storeLogout, refreshToken, isAuthenticated, user, isLoading, setLoading } = useAuthStore();
  const navigate = useNavigate();

  const handleGoogleLogin = useCallback(
    async (idToken: string) => {
      try {
        setLoading(true);
        const tokenResponse = await authService.googleLogin(idToken);
        const tokens = tokenResponse.data;

        // Store tokens temporarily to use in getMe call
        useAuthStore.getState().setTokens(tokens);

        // Fetch user profile
        const userResponse = await userService.getMe();
        const userData = userResponse.data;

        login(userData, tokens);
        navigate('/dashboard');
      } catch (error) {
        console.error('Login failed:', error);
        throw error;
      } finally {
        setLoading(false);
      }
    },
    [login, navigate, setLoading],
  );

  const handleLogout = useCallback(async () => {
    try {
      if (refreshToken) {
        await authService.logout(refreshToken);
      }
    } catch {
      // silently handle
    } finally {
      storeLogout();
      navigate('/login');
    }
  }, [refreshToken, storeLogout, navigate]);

  const checkAuth = useCallback(async () => {
    const state = useAuthStore.getState();
    if (!state.accessToken) {
      setLoading(false);
      return;
    }
    try {
      const response = await userService.getMe();
      useAuthStore.getState().setUser(response.data);
      setLoading(false);
    } catch {
      storeLogout();
    }
  }, [storeLogout, setLoading]);

  return {
    user,
    isAuthenticated,
    isLoading,
    handleGoogleLogin,
    handleLogout,
    checkAuth,
  };
}
