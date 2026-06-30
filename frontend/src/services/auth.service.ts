import axios from 'axios';
import apiClient from './api.client';
import type { ApiResponse, TokenResponse } from '@/types';

export const authService = {
  async googleLogin(idToken: string): Promise<ApiResponse<TokenResponse>> {
    try {
      const response = await apiClient.post<ApiResponse<TokenResponse>>(
        '/api/v1/auth/google',
        { id_token: idToken },
      );
      return response.data;
    } catch (error) {
      if (axios.isAxiosError(error)) {
        const serverMessage =
          (error.response?.data as { message?: string } | undefined)?.message;
        const status = error.response?.status;

        if (!status) {
          throw new Error(
            'Google sign-in could not reach the backend. Check that the API server is running and the proxy/API URL is correct.',
          );
        }

        throw new Error(
          serverMessage ||
            `Google sign-in failed with HTTP ${status}. Make sure the Google client ID, origin, and backend token verification are configured correctly.`,
        );
      }

      throw error;
    }
  },

  async refreshTokens(refreshToken: string): Promise<ApiResponse<TokenResponse>> {
    const response = await apiClient.post<ApiResponse<TokenResponse>>(
      '/api/v1/auth/refresh',
      { refresh_token: refreshToken },
    );
    return response.data;
  },

  async logout(refreshToken: string): Promise<void> {
    await apiClient.post('/api/v1/auth/logout', {
      refresh_token: refreshToken,
    });
  },

  async healthCheck(): Promise<ApiResponse<{ status: string }>> {
    const response = await apiClient.get<ApiResponse<{ status: string }>>(
      '/api/v1/auth/health',
    );
    return response.data;
  },
};
