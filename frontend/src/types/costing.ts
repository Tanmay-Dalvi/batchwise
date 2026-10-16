export interface IngredientInput {
  name: string;
  recipe_quantity: string;
  recipe_unit: string;
  purchase_quantity?: string | null;
  purchase_unit?: string | null;
  purchase_price: string;
}

export interface BatchYieldInput {
  sellable_quantity?: string | null;
  gross_quantity?: string | null;
  scrap_quantity?: string | null;
  scrap_percentage?: string | null;
  unit_name: string;
}

export interface BatchCostingInput {
  batch_name: string;
  ingredients: IngredientInput[];
  packaging_cost: string;
  labour_cost: string;
  fuel_cost: string;
  delivery_cost: string;
  other_expenses: string;
  direct_wastage_expense: string;
  batch_yield: BatchYieldInput;
  planned_selling_price?: string | null;
  target_margin_pct?: string | null;
  actual_units_sold?: string | null;
}

export interface AuditStep {
  step_name: string;
  formula: string;
  inputs: Record<string, string>;
  result: string;
  explanation: string;
}

export interface IngredientCostResult {
  name: string;
  recipe_quantity: string;
  recipe_unit: string;
  purchase_quantity: string;
  purchase_unit: string;
  purchase_price: string;
  cost: string;
  exact_cost: string;
  audit_step: AuditStep;
}

export interface BatchCalculationResult {
  batch_name: string;
  unit_name: string;
  total_ingredients_cost: string;
  packaging_cost: string;
  labour_cost: string;
  fuel_cost: string;
  delivery_cost: string;
  other_expenses: string;
  direct_wastage_expense: string;
  total_overheads: string;
  total_batch_cost: string;
  gross_quantity?: string | null;
  scrap_quantity?: string | null;
  sellable_quantity: string;
  cost_per_sellable_unit: string;
  break_even_price_per_unit: string;
  planned_selling_price?: string | null;
  projected_revenue?: string | null;
  projected_profit?: string | null;
  profit_per_unit?: string | null;
  profit_margin_pct?: string | null;
  markup_pct?: string | null;
  break_even_units_to_sell?: string | null;
  target_margin_pct?: string | null;
  target_margin_selling_price?: string | null;
  target_margin_profit_per_unit?: string | null;
  target_margin_markup_pct?: string | null;
  actual_units_sold?: string | null;
  unsold_units?: string | null;
  realized_revenue?: string | null;
  cogs_sold_units?: string | null;
  realized_gross_profit?: string | null;
  net_cashflow?: string | null;
  unsold_inventory_cost_value?: string | null;
  ingredient_results: IngredientCostResult[];
  audit_trail: AuditStep[];
}

export interface BatchRecordSummary {
  id: string;
  recipe_id?: string | null;
  batch_name: string;
  notes?: string | null;
  total_batch_cost: string;
  sellable_quantity: string;
  unit_name: string;
  cost_per_sellable_unit: string;
  planned_selling_price?: string | null;
  projected_profit?: string | null;
  profit_margin_pct?: string | null;
  created_at: string;
  updated_at: string;
}

export interface BatchRecordDetailResponse extends BatchRecordSummary {
  calculation_input: BatchCostingInput;
  calculation_result: BatchCalculationResult;
}

export interface BatchRecordCreate {
  batch_costing: BatchCostingInput;
  recipe_id?: string | null;
  notes?: string | null;
}

