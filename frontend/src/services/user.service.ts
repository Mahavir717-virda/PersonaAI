import apiClient from './api.client';
import type { ApiResponse, User } from '@/types';

export const userService = {
  async getMe(): Promise<ApiResponse<User>> {
    const response = await apiClient.get<ApiResponse<User>>('/api/v1/users/me');
    return response.data;
  },

  async updateMe(data: {
    full_name?: string;
    avatar_url?: string;
    theme?: string;
    language?: string;
    timezone?: string;
  }): Promise<ApiResponse<User>> {
    const response = await apiClient.patch<ApiResponse<User>>(
      '/api/v1/users/me',
      data,
    );
    return response.data;
  },
};
