import { authService } from '@/lib/auth';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

class AssetManagerAPI {
  async sendMessage(message, chatHistory = [], selectedBrand = null) {
    try {
      const token = authService.token;
      if (!token) {
        throw new Error('No authentication token available');
      }

      const response = await fetch(`${API_BASE_URL}/api/asset-manager/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify({
          message,
          chat_history: chatHistory,
          selected_brand: selectedBrand,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Asset manager API error:', error);
      throw error;
    }
  }
}

export const assetManagerAPI = new AssetManagerAPI();