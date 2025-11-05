/**
 * API Integration Layer - SME AI Vertex
 *
 * Type-safe client for backend FastAPI endpoints.
 * Centralized error handling and request/response transformations.
 *
 * @module lib/api
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080';

/**
 * Generic API error class
 */
export class APIError extends Error {
  constructor(
    message: string,
    public status?: number,
    public detail?: string
  ) {
    super(message);
    this.name = 'APIError';
  }
}

/**
 * Type-safe fetch wrapper with error handling
 */
async function apiFetch<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options?.headers,
      },
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || errorDetail;
      } catch {
        // Ignore JSON parse errors
      }

      throw new APIError(
        `API request failed: ${errorDetail}`,
        response.status,
        errorDetail
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    // Network error or other unexpected error
    throw new APIError(
      error instanceof Error ? error.message : 'Unknown error occurred',
      undefined,
      'Network error'
    );
  }
}

/**
 * Multipart form data upload wrapper
 */
async function apiUpload<T>(
  endpoint: string,
  formData: FormData
): Promise<T> {
  const url = `${API_BASE_URL}${endpoint}`;

  try {
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
      // Don't set Content-Type - browser will set it with boundary
    });

    if (!response.ok) {
      let errorDetail = `HTTP ${response.status}`;
      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.message || errorDetail;
      } catch {
        // Ignore JSON parse errors
      }

      throw new APIError(
        `Upload failed: ${errorDetail}`,
        response.status,
        errorDetail
      );
    }

    return await response.json();
  } catch (error) {
    if (error instanceof APIError) {
      throw error;
    }

    throw new APIError(
      error instanceof Error ? error.message : 'Unknown error occurred',
      undefined,
      'Network error'
    );
  }
}

// ============================================================================
// TYPE DEFINITIONS
// ============================================================================

export interface HealthCheck {
  status: 'healthy' | 'unhealthy';
  timestamp: string;
  version: string;
  services: Record<string, string>;
}

export interface AnalysisUploadResponse {
  analysis_id: string;
  status: 'processing' | 'completed' | 'failed';
  uploaded_at: string;
  drawing_filename: string;
  project_name?: string;
}

export interface AnalysisInfo {
  analysis_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  drawing_filename: string;
  project_name?: string;
  quality_mode: 'flash' | 'pro';
  exception_count?: number;
  created_at: string;
  completed_at?: string;
}

export interface ReportResponse {
  report_url: string;
  report_type: 'executive' | 'detailed';
  generated_at: string;
}

export interface KnowledgeBaseDocument {
  document_id: string;
  filename: string;
  document_type: 'manual' | 'specification' | 'quality_manual';
  file_size: number;
  upload_date: string;
  status: 'pending' | 'processing' | 'indexed' | 'failed';
  pages_indexed?: number;
}

export interface KnowledgeBaseStats {
  total_documents: number;
  total_pages_indexed: number;
  documents_by_type: Record<string, number>;
  last_updated: string;
}

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  history: ChatMessage[];
}

export interface ChatResponse {
  message: string;
  response: string;
  sources?: Array<{
    title: string;
    uri?: string;
    type?: string;
  }>;
}

// ============================================================================
// ANALYSIS API
// ============================================================================

export const analysisAPI = {
  /**
   * Upload a technical drawing for analysis
   */
  uploadDrawing: async (
    file: File,
    projectName?: string,
    qualityMode: 'flash' | 'pro' = 'flash'
  ): Promise<AnalysisUploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    if (projectName) {
      formData.append('project_name', projectName);
    }

    formData.append('quality_mode', qualityMode);

    return apiUpload<AnalysisUploadResponse>('/analysis/upload', formData);
  },

  /**
   * List all analyses
   */
  listAnalyses: async (): Promise<AnalysisInfo[]> => {
    return apiFetch<AnalysisInfo[]>('/analysis/documents');
  },

  /**
   * Get analysis details by ID
   */
  getAnalysis: async (analysisId: string): Promise<AnalysisInfo> => {
    return apiFetch<AnalysisInfo>(`/analysis/${analysisId}`);
  },

  /**
   * Get analysis report (executive or detailed)
   */
  getReport: async (
    analysisId: string,
    reportType: 'executive' | 'detailed' = 'executive'
  ): Promise<ReportResponse> => {
    return apiFetch<ReportResponse>(
      `/analysis/${analysisId}/report?report_type=${reportType}`
    );
  },

  /**
   * Delete an analysis
   */
  deleteAnalysis: async (analysisId: string): Promise<void> => {
    await apiFetch<void>(`/analysis/${analysisId}`, {
      method: 'DELETE',
    });
  },
};

// ============================================================================
// KNOWLEDGE BASE API
// ============================================================================

export const knowledgeBaseAPI = {
  /**
   * Upload a document to the knowledge base
   */
  uploadDocument: async (
    file: File,
    documentType: 'manual' | 'specification' | 'quality_manual' = 'manual'
  ): Promise<KnowledgeBaseDocument> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', documentType);

    return apiUpload<KnowledgeBaseDocument>('/knowledgebase/upload', formData);
  },

  /**
   * List all documents in the knowledge base
   */
  listDocuments: async (): Promise<KnowledgeBaseDocument[]> => {
    return apiFetch<KnowledgeBaseDocument[]>('/knowledgebase/documents');
  },

  /**
   * Get document details by ID
   */
  getDocument: async (documentId: string): Promise<KnowledgeBaseDocument> => {
    return apiFetch<KnowledgeBaseDocument>(`/knowledgebase/documents/${documentId}`);
  },

  /**
   * Delete a document from the knowledge base
   */
  deleteDocument: async (documentId: string): Promise<void> => {
    await apiFetch<void>(`/knowledgebase/documents/${documentId}`, {
      method: 'DELETE',
    });
  },

  /**
   * Get knowledge base statistics
   */
  getStats: async (): Promise<KnowledgeBaseStats> => {
    return apiFetch<KnowledgeBaseStats>('/knowledgebase/stats');
  },
};

// ============================================================================
// CHAT API
// ============================================================================

export const chatAPI = {
  /**
   * Send a chat message (text only)
   */
  sendMessage: async (
    message: string,
    history: ChatMessage[] = []
  ): Promise<ChatResponse> => {
    return apiFetch<ChatResponse>('/analysis/', {
      method: 'POST',
      body: JSON.stringify({ message, chat_history: history }),
    });
  },

  /**
   * Upload file with chat message (unified chat endpoint)
   */
  uploadWithChat: async (
    file: File,
    message: string,
    history: ChatMessage[] = []
  ): Promise<ChatResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', message);
    formData.append('chat_history', JSON.stringify(history));

    return apiUpload<ChatResponse>('/analysis/upload', formData);
  },
};

// ============================================================================
// HEALTH API
// ============================================================================

export const healthAPI = {
  /**
   * Check API health
   */
  check: async (): Promise<HealthCheck> => {
    return apiFetch<HealthCheck>('/health');
  },
};

// ============================================================================
// EXPORTS
// ============================================================================

export default {
  analysisAPI,
  knowledgeBaseAPI,
  chatAPI,
  healthAPI,
};
