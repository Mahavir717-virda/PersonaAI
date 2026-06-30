import { useEffect } from 'react';
import { RouterProvider } from 'react-router-dom';
import { Toaster } from 'sonner';
import { AppProviders } from './providers';
import { router } from '@/routes';
import { useAuthStore } from '@/store/auth.store';
import { userService } from '@/services/user.service';

export function App() {
  const { accessToken, setUser, logout, setLoading, isAuthenticated } = useAuthStore();

  useEffect(() => {
    async function initializeAuth() {
      if (!accessToken || !isAuthenticated) {
        setLoading(false);
        return;
      }
      try {
        const response = await userService.getMe();
        setUser(response.data);
      } catch (error) {
        console.error('Failed to restore session:', error);
        logout();
      } finally {
        setLoading(false);
      }
    }
    initializeAuth();
  }, [accessToken, isAuthenticated, setUser, logout, setLoading]);

  return (
    <AppProviders>
      <RouterProvider router={router} />
      <Toaster position="top-right" richColors theme="dark" />
    </AppProviders>
  );
}
export default App;
