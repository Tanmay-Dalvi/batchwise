export interface CandidateIngredient {
  name: string;
  recipe_quantity?: string | null;
  recipe_unit?: string | null;
  purchase_quantity?: string | null;
  purchase_unit?: string | null;
  purchase_price?: string | null;
  is_ambiguous?: boolean;
  ambiguity_reason?: string | null;
}

export interface AmbiguityFlag {
  field_name: string;
  raw_text: string;
  question: string;
  options: string[];
}

export interface CandidateBatchExtraction {
  raw_note: string;
  batch_name?: string | null;
  ingredients: CandidateIngredient[];
  packaging_cost?: string | null;
  labour_cost?: string | null;
  fuel_cost?: string | null;
  delivery_cost?: string | null;
  other_expenses?: string | null;
  sellable_quantity?: string | null;
  yield_unit_name?: string | null;
  planned_selling_price?: string | null;
  missing_fields: string[];
  ambiguities: AmbiguityFlag[];
  confidence_summary: string;
  can_calculate: boolean;
}

export interface ParseNoteRequest {
  note: string;
}

export interface ParseNoteResponse {
  success: boolean;
  status: 'success' | 'partial' | 'error';
  candidate?: CandidateBatchExtraction | null;
  error_message?: string | null;
  model_used?: string | null;
  provider_used?: 'gemini' | 'ollama' | string | null;
}

export interface AiStatusResponse {
  provider: 'gemini' | 'ollama';
  model: string;
  is_configured: boolean;
  description: string;
}

