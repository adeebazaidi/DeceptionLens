const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

export const documentApi = {
  analyzeDocument: async (file) => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/document/analyze`, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => null);
      throw new Error(errorData?.detail || 'Failed to analyze document');
    }

    return response.json();
  }
};
