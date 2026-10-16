export interface RecipeIngredientBase {
  name: string;
  recipe_quantity: string;
  recipe_unit: string;
  purchase_quantity?: string | null;
  purchase_unit?: string | null;
  purchase_price: string;
}

export type RecipeIngredientCreate = RecipeIngredientBase;

export interface RecipeIngredientResponse extends RecipeIngredientBase {
  id: string;
  recipe_id: string;
  purchase_quantity: string;
  purchase_unit: string;
}

export interface RecipeCreate {
  name: string;
  description?: string | null;
  yield_unit?: string;
  default_packaging_cost?: string;
  default_labour_cost?: string;
  default_fuel_cost?: string;
  default_delivery_cost?: string;
  default_other_expenses?: string;
  ingredients: RecipeIngredientCreate[];
}

export interface RecipeUpdate {
  name?: string;
  description?: string | null;
  yield_unit?: string;
  default_packaging_cost?: string;
  default_labour_cost?: string;
  default_fuel_cost?: string;
  default_delivery_cost?: string;
  default_other_expenses?: string;
  ingredients?: RecipeIngredientCreate[];
}

export interface RecipeResponse {
  id: string;
  name: string;
  description?: string | null;
  yield_unit: string;
  default_packaging_cost: string;
  default_labour_cost: string;
  default_fuel_cost: string;
  default_delivery_cost: string;
  default_other_expenses: string;
  created_at: string;
  updated_at: string;
  ingredients: RecipeIngredientResponse[];
}

