import {
  BatchCalculationResult,
  BatchCostingInput,
  BatchRecordCreate,
  BatchRecordDetailResponse,
  BatchRecordSummary,
} from '../types/costing';
import { ParseNoteResponse } from '../types/ai';
import {
  RecipeCreate,
  RecipeResponse,
  RecipeUpdate,
} from '../types/recipe';

const rawBase = import.meta.env.VITE_API_BASE_URL || '/api/v1';
const API_BASE = rawBase.replace(/\/+$/, '');

export class ApiError extends Error {
  public status: number;
  public errorType?: string;

  constructor(message: string, status: number, errorType?: string) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.errorType = errorType;
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {}),
  };

  try {
    const response = await fetch(url, { ...options, headers });

    if (response.status === 204) {
      return {} as T;
    }

    const data = await response.json().catch(() => null);

    if (!response.ok) {
      let message = 'An unexpected server error occurred.';
      let errorType = 'ServerError';

      if (data && data.detail) {
        if (typeof data.detail === 'object' && data.detail.message) {
          message = data.detail.message;
          errorType = data.detail.error_type || errorType;
        } else if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail)) {
          // Pydantic validation error array
          const firstErr = data.detail[0];
          message = firstErr ? `${firstErr.loc ? firstErr.loc.join(' -> ') : 'Field'}: ${firstErr.msg}` : message;
        }
      }

      throw new ApiError(message, response.status, errorType);
    }

    return data as T;
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    // Network failure or CORS block
    throw new ApiError(
      'Unable to connect to the Batchwise server. Please check your backend connection.',
      0,
      'NetworkError'
    );
  }
}

export const api = {
  // System Health
  async getHealth(): Promise<{ status: string; app: string; database: string }> {
    return request('/health');
  },

  // Deterministic Costing
  async calculateBatch(input: BatchCostingInput): Promise<BatchCalculationResult> {
    return request('/calculate', {
      method: 'POST',
      body: JSON.stringify(input),
    });
  },

  // AI Note Parser
  async parseNote(note: string): Promise<ParseNoteResponse> {
    return request('/parse-note', {
      method: 'POST',
      body: JSON.stringify({ note }),
    });
  },

  // Recipe Templates
  async listRecipes(): Promise<RecipeResponse[]> {
    return request('/recipes');
  },

  async createRecipe(recipe: RecipeCreate): Promise<RecipeResponse> {
    return request('/recipes', {
      method: 'POST',
      body: JSON.stringify(recipe),
    });
  },

  async getRecipe(id: string): Promise<RecipeResponse> {
    return request(`/recipes/${id}`);
  },

  async updateRecipe(id: string, recipe: RecipeUpdate): Promise<RecipeResponse> {
    return request(`/recipes/${id}`, {
      method: 'PUT',
      body: JSON.stringify(recipe),
    });
  },

  async deleteRecipe(id: string): Promise<void> {
    return request(`/recipes/${id}`, {
      method: 'DELETE',
    });
  },

  // Production Batches
  async listBatches(recipeId?: string): Promise<BatchRecordSummary[]> {
    const query = recipeId ? `?recipe_id=${encodeURIComponent(recipeId)}` : '';
    return request(`/batches${query}`);
  },

  async createBatch(batch: BatchRecordCreate): Promise<BatchRecordDetailResponse> {
    return request('/batches', {
      method: 'POST',
      body: JSON.stringify(batch),
    });
  },

  async getBatch(id: string): Promise<BatchRecordDetailResponse> {
    return request(`/batches/${id}`);
  },

  async updateBatch(id: string, batch: BatchRecordCreate): Promise<BatchRecordDetailResponse> {
    return request(`/batches/${id}`, {
      method: 'PUT',
      body: JSON.stringify(batch),
    });
  },

  async deleteBatch(id: string): Promise<void> {
    return request(`/batches/${id}`, {
      method: 'DELETE',
    });
  },
};

