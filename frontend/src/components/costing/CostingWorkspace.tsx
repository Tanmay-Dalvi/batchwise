import React, { useState, useEffect } from 'react';
import {
  BatchCostingInput,
  BatchCalculationResult,
  IngredientInput,
} from '../../types/costing';
import { RecipeResponse } from '../../types/recipe';
import { api, ApiError } from '../../lib/api';
import { formatRupee } from '../../lib/currency';
import { CostSummaryCard } from './CostSummaryCard';
import { PricingScenarioSlider } from './PricingScenarioSlider';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import {
  Plus,
  Trash2,
  Calculator,
  BookmarkPlus,
  AlertTriangle,
  CheckCircle2,
  Layers,
  ChevronDown,
  Sparkles,
} from 'lucide-react';

interface CostingWorkspaceProps {
  initialData?: Partial<BatchCostingInput>;
  onBatchSaved?: (batchId: string) => void;
  onOpenAiNotes?: () => void;
}

const COMMON_UNITS = [
  { value: 'kg', label: 'Kilograms (kg)', category: 'Mass' },
  { value: 'g', label: 'Grams (g)', category: 'Mass' },
  { value: 'L', label: 'Litres (L)', category: 'Volume' },
  { value: 'ml', label: 'Millilitres (ml)', category: 'Volume' },
  { value: 'units', label: 'Units / Pieces', category: 'Count' },
  { value: 'dozens', label: 'Dozens', category: 'Count' },
  { value: 'packets', label: 'Packets', category: 'Count' },
];

export const CostingWorkspace: React.FC<CostingWorkspaceProps> = ({
  initialData,
  onBatchSaved,
  onOpenAiNotes,
}) => {
  // Form State
  const [batchName, setBatchName] = useState<string>(
    initialData?.batch_name || 'Besan Ladoo Batch'
  );
  const [selectedRecipeId, setSelectedRecipeId] = useState<string>('');
  const [recipes, setRecipes] = useState<RecipeResponse[]>([]);

  // Ingredients State
  const [ingredients, setIngredients] = useState<IngredientInput[]>(
    initialData?.ingredients?.length
      ? initialData.ingredients
      : [
          {
            name: 'Besan (Gram Flour)',
            recipe_quantity: '5',
            recipe_unit: 'kg',
            purchase_quantity: '5',
            purchase_unit: 'kg',
            purchase_price: '600',
          },
          {
            name: 'Refined Oil / Ghee',
            recipe_quantity: '1',
            recipe_unit: 'L',
            purchase_quantity: '1',
            purchase_unit: 'L',
            purchase_price: '180',
          },
        ]
  );

  // Overheads State
  const [packagingCost, setPackagingCost] = useState<string>(
    initialData?.packaging_cost || '80'
  );
  const [labourCost, setLabourCost] = useState<string>(
    initialData?.labour_cost || '0'
  );
  const [fuelCost, setFuelCost] = useState<string>(
    initialData?.fuel_cost || '0'
  );
  const [deliveryCost, setDeliveryCost] = useState<string>(
    initialData?.delivery_cost || '0'
  );
  const [otherExpenses, setOtherExpenses] = useState<string>(
    initialData?.other_expenses || '0'
  );
  const [directWastageExpense, setDirectWastageExpense] = useState<string>(
    initialData?.direct_wastage_expense || '0'
  );

  // Yield & Pricing State
  const [unitName, setUnitName] = useState<string>(
    initialData?.batch_yield?.unit_name || 'packets'
  );
  const [sellableQuantity, setSellableQuantity] = useState<string>(
    initialData?.batch_yield?.sellable_quantity || '75'
  );
  const [grossQuantity, setGrossQuantity] = useState<string>(
    initialData?.batch_yield?.gross_quantity || ''
  );
  const [scrapQuantity, setScrapQuantity] = useState<string>(
    initialData?.batch_yield?.scrap_quantity || ''
  );
  const [plannedSellingPrice, setPlannedSellingPrice] = useState<string>(
    initialData?.planned_selling_price || '25'
  );
  const [targetMarginPct, setTargetMarginPct] = useState<string>(
    initialData?.target_margin_pct || '40'
  );

  // Operational State
  const [isCalculating, setIsCalculating] = useState(false);
  const [isSavingBatch, setIsSavingBatch] = useState(false);
  const [isSavingRecipe, setIsSavingRecipe] = useState(false);
  const [calculationResult, setCalculationResult] =
    useState<BatchCalculationResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load available recipes for the dropdown
  useEffect(() => {
    async function fetchRecipes() {
      try {
        const list = await api.listRecipes();
        setRecipes(list);
      } catch (err) {
        console.error('Failed to load recipes list', err);
      }
    }
    fetchRecipes();
  }, []);

  // Update form if initialData changes (e.g. from AI review modal)
  useEffect(() => {
    if (initialData) {
      if (initialData.batch_name) setBatchName(initialData.batch_name);
      if (initialData.ingredients?.length) setIngredients(initialData.ingredients);
      if (initialData.packaging_cost !== undefined) setPackagingCost(initialData.packaging_cost);
      if (initialData.labour_cost !== undefined) setLabourCost(initialData.labour_cost);
      if (initialData.fuel_cost !== undefined) setFuelCost(initialData.fuel_cost);
      if (initialData.delivery_cost !== undefined) setDeliveryCost(initialData.delivery_cost);
      if (initialData.other_expenses !== undefined) setOtherExpenses(initialData.other_expenses);
      if (initialData.direct_wastage_expense !== undefined)
        setDirectWastageExpense(initialData.direct_wastage_expense);
      if (initialData.batch_yield?.unit_name) setUnitName(initialData.batch_yield.unit_name);
      if (initialData.batch_yield?.sellable_quantity)
        setSellableQuantity(initialData.batch_yield.sellable_quantity);
      if (initialData.planned_selling_price !== undefined)
        setPlannedSellingPrice(initialData.planned_selling_price || '');
      if (initialData.target_margin_pct !== undefined)
        setTargetMarginPct(initialData.target_margin_pct || '');
    }
  }, [initialData]);

  // Load selected recipe into workspace
  const handleLoadRecipe = (recipeId: string) => {
    setSelectedRecipeId(recipeId);
    if (!recipeId) return;

    const found = recipes.find((r) => r.id === recipeId);
    if (!found) return;

    setBatchName(`${found.name} Batch`);
    setUnitName(found.yield_unit || 'packets');
    setPackagingCost(found.default_packaging_cost || '0');
    setLabourCost(found.default_labour_cost || '0');
    setFuelCost(found.default_fuel_cost || '0');
    setDeliveryCost(found.default_delivery_cost || '0');
    setOtherExpenses(found.default_other_expenses || '0');

    if (found.ingredients && found.ingredients.length > 0) {
      setIngredients(
        found.ingredients.map((ing) => ({
          name: ing.name,
          recipe_quantity: ing.recipe_quantity,
          recipe_unit: ing.recipe_unit,
          purchase_quantity: ing.purchase_quantity || ing.recipe_quantity,
          purchase_unit: ing.purchase_unit || ing.recipe_unit,
          purchase_price: ing.purchase_price,
        }))
      );
    }
    setSuccessMessage(`Loaded recipe "${found.name}" successfully.`);
    setTimeout(() => setSuccessMessage(null), 3000);
  };

  // Ingredient Helpers
  const handleAddIngredient = () => {
    setIngredients([
      ...ingredients,
      {
        name: '',
        recipe_quantity: '1',
        recipe_unit: 'kg',
        purchase_quantity: '1',
        purchase_unit: 'kg',
        purchase_price: '0',
      },
    ]);
  };

  const handleUpdateIngredient = (index: number, field: keyof IngredientInput, value: string) => {
    const updated = [...ingredients];
    updated[index] = { ...updated[index], [field]: value };
    // Auto-sync purchase unit with recipe unit if empty
    if (field === 'recipe_unit' && (!updated[index].purchase_unit || updated[index].purchase_unit === '')) {
      updated[index].purchase_unit = value;
    }
    setIngredients(updated);
  };

  const handleRemoveIngredient = (index: number) => {
    if (ingredients.length <= 1) {
      setErrorMessage('A batch must have at least one ingredient.');
      return;
    }
    setIngredients(ingredients.filter((_, i) => i !== index));
  };

  // Build current costing payload
  const buildPayload = (): BatchCostingInput => {
    return {
      batch_name: batchName.trim() || 'Untitled Batch',
      ingredients: ingredients.map((ing) => ({
        name: ing.name.trim() || 'Ingredient',
        recipe_quantity: ing.recipe_quantity || '0',
        recipe_unit: ing.recipe_unit || 'kg',
        purchase_quantity: ing.purchase_quantity || ing.recipe_quantity || '1',
        purchase_unit: ing.purchase_unit || ing.recipe_unit || 'kg',
        purchase_price: ing.purchase_price || '0',
      })),
      packaging_cost: packagingCost || '0',
      labour_cost: labourCost || '0',
      fuel_cost: fuelCost || '0',
      delivery_cost: deliveryCost || '0',
      other_expenses: otherExpenses || '0',
      direct_wastage_expense: directWastageExpense || '0',
      batch_yield: {
        unit_name: unitName.trim() || 'packets',
        sellable_quantity: sellableQuantity.trim() || null,
        gross_quantity: grossQuantity.trim() || null,
        scrap_quantity: scrapQuantity.trim() || null,
      },
      planned_selling_price: plannedSellingPrice.trim() || null,
      target_margin_pct: targetMarginPct.trim() || null,
    };
  };

  // Trigger Calculation
  const handleCalculate = async () => {
    setErrorMessage(null);
    setIsCalculating(true);

    try {
      const payload = buildPayload();
      const res = await api.calculateBatch(payload);
      setCalculationResult(res);
    } catch (err: any) {
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage('Failed to calculate batch costs. Please check inputs.');
      }
    } finally {
      setIsCalculating(false);
    }
  };

  // Save current configuration as a reusable recipe
  const handleSaveAsRecipe = async () => {
    setErrorMessage(null);
    setIsSavingRecipe(true);

    try {
      const payload = {
        name: batchName.trim() || 'New Recipe',
        description: `Created from batch on ${new Date().toLocaleDateString()}`,
        yield_unit: unitName.trim() || 'packets',
        default_packaging_cost: packagingCost || '0',
        default_labour_cost: labourCost || '0',
        default_fuel_cost: fuelCost || '0',
        default_delivery_cost: deliveryCost || '0',
        default_other_expenses: otherExpenses || '0',
        ingredients: ingredients.map((ing) => ({
          name: ing.name.trim() || 'Ingredient',
          recipe_quantity: ing.recipe_quantity || '0',
          recipe_unit: ing.recipe_unit || 'kg',
          purchase_quantity: ing.purchase_quantity || ing.recipe_quantity || '1',
          purchase_unit: ing.purchase_unit || ing.recipe_unit || 'kg',
          purchase_price: ing.purchase_price || '0',
        })),
      };

      const saved = await api.createRecipe(payload);
      setRecipes((prev) => [...prev, saved]);
      setSelectedRecipeId(saved.id);
      setSuccessMessage(`Recipe "${saved.name}" saved successfully!`);
      setTimeout(() => setSuccessMessage(null), 3500);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to save recipe.');
    } finally {
      setIsSavingRecipe(false);
    }
  };

  // Save batch record to SQLite
  const handleSaveBatchRecord = async () => {
    if (!calculationResult) {
      setErrorMessage('Please calculate the batch first before saving.');
      return;
    }

    setErrorMessage(null);
    setIsSavingBatch(true);

    try {
      const payload = {
        batch_costing: buildPayload(),
        recipe_id: selectedRecipeId || null,
        notes: `Recorded on ${new Date().toLocaleString()}`,
      };

      const record = await api.createBatch(payload);
      setSuccessMessage(`Batch "${record.batch_name}" successfully recorded in history!`);
      if (onBatchSaved) {
        onBatchSaved(record.id);
      }
      setTimeout(() => setSuccessMessage(null), 4000);
    } catch (err: any) {
      setErrorMessage(err.message || 'Failed to record batch history.');
    } finally {
      setIsSavingBatch(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Workspace Top Header */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm">
        <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 pb-4 border-b border-stone-100">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-forest-700">
              Interactive Workspace
            </span>
            <h2 className="text-xl sm:text-2xl font-bold font-serif text-stone-900">
              Batch Costing Engine
            </h2>
            <p className="text-xs sm:text-sm text-stone-600">
              Deterministic precision: Every batch, every cost, every rupee.
            </p>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            {onOpenAiNotes && (
              <Button
                variant="outline"
                size="sm"
                onClick={onOpenAiNotes}
                className="w-full sm:w-auto text-forest-800 border-forest-200 hover:bg-forest-50"
              >
                <Sparkles className="w-4 h-4 mr-1.5 text-lime-600" />
                Paste Messy Notes
              </Button>
            )}
            <Button
              variant="outline"
              size="sm"
              onClick={handleSaveAsRecipe}
              disabled={isSavingRecipe}
              className="w-full sm:w-auto text-stone-700"
            >
              <BookmarkPlus className="w-4 h-4 mr-1.5 text-stone-500" />
              {isSavingRecipe ? 'Saving...' : 'Save as Recipe'}
            </Button>
          </div>
        </div>

        {/* Batch Name & Recipe Preset Selector */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-4">
          <div className="sm:col-span-2">
            <Input
              label="Batch Name / Description"
              value={batchName}
              onChange={(e) => setBatchName(e.target.value)}
              placeholder="e.g. Besan Ladoo 75-pack batch"
            />
          </div>

          <div>
            <label className="text-xs font-medium text-stone-700 block mb-1">
              Load From Saved Recipe
            </label>
            <div className="relative">
              <select
                value={selectedRecipeId}
                onChange={(e) => handleLoadRecipe(e.target.value)}
                className="w-full text-xs sm:text-sm px-3 py-2 rounded-lg border border-stone-200 bg-white text-stone-800 appearance-none focus:outline-none focus:ring-2 focus:ring-forest-600 focus:border-forest-600 pr-8"
              >
                <option value="">-- Choose saved recipe --</option>
                {recipes.map((r) => (
                  <option key={r.id} value={r.id}>
                    {r.name} ({r.ingredients.length} ingredients)
                  </option>
                ))}
              </select>
              <ChevronDown className="w-4 h-4 text-stone-400 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
            </div>
          </div>
        </div>
      </div>

      {/* Alert Messages */}
      {errorMessage && (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl flex items-start gap-3 text-rose-900 text-sm">
          <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <strong>Calculation Error:</strong> {errorMessage}
          </div>
          <button
            onClick={() => setErrorMessage(null)}
            className="text-rose-500 hover:text-rose-700 font-bold ml-2 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {successMessage && (
        <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl flex items-start gap-3 text-emerald-900 text-sm">
          <CheckCircle2 className="w-5 h-5 text-emerald-600 shrink-0 mt-0.5" />
          <div className="flex-1">{successMessage}</div>
          <button
            onClick={() => setSuccessMessage(null)}
            className="text-emerald-500 hover:text-emerald-700 font-bold ml-2 text-xs"
          >
            Dismiss
          </button>
        </div>
      )}

      {/* Section 1: Ingredients */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="text-base font-semibold text-stone-900 flex items-center gap-2">
              <Layers className="w-4 h-4 text-forest-700" />
              1. Ingredients & Raw Materials
            </h3>
            <p className="text-xs text-stone-500">
              Purchase quantity & price are converted automatically to recipe batch usage.
            </p>
          </div>
          <Button
            variant="outline"
            size="sm"
            onClick={handleAddIngredient}
            className="text-forest-800 border-forest-300"
          >
            <Plus className="w-4 h-4 mr-1 text-forest-700" />
            Add Row
          </Button>
        </div>

        <div className="space-y-3">
          {ingredients.map((ing, idx) => (
            <div
              key={idx}
              className="p-3 bg-stone-50 rounded-lg border border-stone-200 grid grid-cols-1 sm:grid-cols-12 gap-2.5 items-end"
            >
              <div className="sm:col-span-4">
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Ingredient Name
                </label>
                <input
                  type="text"
                  value={ing.name}
                  onChange={(e) => handleUpdateIngredient(idx, 'name', e.target.value)}
                  placeholder="e.g. Besan, Ghee, Sugar"
                  className="w-full text-xs px-2.5 py-1.5 rounded border border-stone-300 bg-white focus:outline-none focus:ring-1 focus:ring-forest-600"
                />
              </div>

              <div className="sm:col-span-2">
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Batch Qty & Unit
                </label>
                <div className="flex gap-1">
                  <input
                    type="number"
                    step="any"
                    value={ing.recipe_quantity}
                    onChange={(e) => handleUpdateIngredient(idx, 'recipe_quantity', e.target.value)}
                    placeholder="5"
                    className="w-16 text-xs px-2 py-1.5 rounded border border-stone-300 bg-white focus:outline-none focus:ring-1 focus:ring-forest-600"
                  />
                  <select
                    value={ing.recipe_unit}
                    onChange={(e) => handleUpdateIngredient(idx, 'recipe_unit', e.target.value)}
                    className="flex-1 text-xs px-1.5 py-1.5 rounded border border-stone-300 bg-white"
                  >
                    {COMMON_UNITS.map((u) => (
                      <option key={u.value} value={u.value}>
                        {u.value}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="sm:col-span-3">
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Pack Size Purchased
                </label>
                <div className="flex gap-1">
                  <input
                    type="number"
                    step="any"
                    value={ing.purchase_quantity || ''}
                    onChange={(e) => handleUpdateIngredient(idx, 'purchase_quantity', e.target.value)}
                    placeholder="1"
                    className="w-16 text-xs px-2 py-1.5 rounded border border-stone-300 bg-white focus:outline-none focus:ring-1 focus:ring-forest-600"
                  />
                  <select
                    value={ing.purchase_unit || ing.recipe_unit}
                    onChange={(e) => handleUpdateIngredient(idx, 'purchase_unit', e.target.value)}
                    className="flex-1 text-xs px-1.5 py-1.5 rounded border border-stone-300 bg-white"
                  >
                    {COMMON_UNITS.map((u) => (
                      <option key={u.value} value={u.value}>
                        {u.value}
                      </option>
                    ))}
                  </select>
                </div>
              </div>

              <div className="sm:col-span-2">
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Pack Cost (₹)
                </label>
                <div className="relative">
                  <span className="absolute left-2 top-1/2 -translate-y-1/2 text-stone-400 text-xs">
                    ₹
                  </span>
                  <input
                    type="number"
                    step="any"
                    value={ing.purchase_price}
                    onChange={(e) => handleUpdateIngredient(idx, 'purchase_price', e.target.value)}
                    placeholder="600"
                    className="w-full text-xs pl-5 pr-2 py-1.5 rounded border border-stone-300 bg-white focus:outline-none focus:ring-1 focus:ring-forest-600"
                  />
                </div>
              </div>

              <div className="sm:col-span-1 flex justify-end">
                <button
                  type="button"
                  onClick={() => handleRemoveIngredient(idx)}
                  className="p-1.5 text-stone-400 hover:text-rose-600 rounded transition-colors"
                  title="Remove ingredient"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Section 2: Overheads & Operating Expenses */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm space-y-4">
        <div>
          <h3 className="text-base font-semibold text-stone-900">
            2. Batch Overheads & Operational Expenses
          </h3>
          <p className="text-xs text-stone-500">
            Add packaging, fuel, delivery, and labour to calculate your real batch cost.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-3">
          <Input
            label="Packaging (₹)"
            type="number"
            step="any"
            value={packagingCost}
            onChange={(e) => setPackagingCost(e.target.value)}
            placeholder="0"
          />
          <Input
            label="Labour (₹)"
            type="number"
            step="any"
            value={labourCost}
            onChange={(e) => setLabourCost(e.target.value)}
            placeholder="0"
          />
          <Input
            label="Fuel / Gas (₹)"
            type="number"
            step="any"
            value={fuelCost}
            onChange={(e) => setFuelCost(e.target.value)}
            placeholder="0"
          />
          <Input
            label="Delivery (₹)"
            type="number"
            step="any"
            value={deliveryCost}
            onChange={(e) => setDeliveryCost(e.target.value)}
            placeholder="0"
          />
          <Input
            label="Other Overheads (₹)"
            type="number"
            step="any"
            value={otherExpenses}
            onChange={(e) => setOtherExpenses(e.target.value)}
            placeholder="0"
          />
          <Input
            label="Direct Wastage (₹)"
            type="number"
            step="any"
            value={directWastageExpense}
            onChange={(e) => setDirectWastageExpense(e.target.value)}
            placeholder="0"
          />
        </div>
      </div>

      {/* Section 3: Yield, Selling Price, and Target Margin */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm space-y-4">
        <div>
          <h3 className="text-base font-semibold text-stone-900">
            3. Production Yield & Planned Pricing
          </h3>
          <p className="text-xs text-stone-500">
            Define units produced and test your selling price or target profit margin.
          </p>
        </div>

        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <Input
            label="Unit Type"
            value={unitName}
            onChange={(e) => setUnitName(e.target.value)}
            placeholder="packets, boxes, pieces"
          />
          <Input
            label="Sellable Quantity"
            type="number"
            step="any"
            value={sellableQuantity}
            onChange={(e) => setSellableQuantity(e.target.value)}
            placeholder="e.g. 75"
          />
          <Input
            label="Selling Price / Unit (₹)"
            type="number"
            step="any"
            value={plannedSellingPrice}
            onChange={(e) => setPlannedSellingPrice(e.target.value)}
            placeholder="e.g. 25"
          />
          <Input
            label="Target Margin (%)"
            type="number"
            step="any"
            value={targetMarginPct}
            onChange={(e) => setTargetMarginPct(e.target.value)}
            placeholder="e.g. 40"
          />
        </div>

        {/* Optional scrap inputs */}
        <div className="pt-2 border-t border-stone-100 flex flex-wrap gap-4 text-xs text-stone-600">
          <div className="flex items-center gap-2">
            <span>Optional gross yield:</span>
            <input
              type="number"
              value={grossQuantity}
              onChange={(e) => setGrossQuantity(e.target.value)}
              placeholder="Total made"
              className="w-24 px-2 py-1 rounded border border-stone-300 text-xs"
            />
          </div>
          <div className="flex items-center gap-2">
            <span>Discarded/Scrap units:</span>
            <input
              type="number"
              value={scrapQuantity}
              onChange={(e) => setScrapQuantity(e.target.value)}
              placeholder="Damaged"
              className="w-24 px-2 py-1 rounded border border-stone-300 text-xs"
            />
          </div>
        </div>
      </div>

      {/* Main Calculate Action Button */}
      <div className="flex justify-center pt-2">
        <Button
          variant="primary"
          size="lg"
          onClick={handleCalculate}
          disabled={isCalculating}
          className="w-full sm:w-80 shadow-md py-3 text-base font-semibold bg-forest-900 hover:bg-forest-950 text-white"
        >
          <Calculator className="w-5 h-5 mr-2 text-lime-400" />
          {isCalculating ? 'Computing Costs...' : 'Calculate Batch Cost & Profit'}
        </Button>
      </div>

      {/* Results Display */}
      {calculationResult && (
        <div className="space-y-6 pt-4 animate-fadeIn">
          <CostSummaryCard
            result={calculationResult}
            onSaveBatch={handleSaveBatchRecord}
            isSaving={isSavingBatch}
          />

          {/* Interactive Pricing Scenario Simulator */}
          <PricingScenarioSlider
            currentSellingPrice={plannedSellingPrice}
            currentTargetMargin={targetMarginPct}
            onPriceChange={(val) => setPlannedSellingPrice(val)}
            onMarginChange={(val) => setTargetMarginPct(val)}
            onApplyScenario={handleCalculate}
            isCalculating={isCalculating}
          />

          {/* Detailed Ingredient Cost Breakdown Table */}
          {calculationResult.ingredient_results?.length > 0 && (
            <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm overflow-x-auto">
              <h4 className="text-sm font-semibold text-stone-900 mb-3">
                Calculated Ingredient Cost Breakdown
              </h4>
              <table className="w-full text-xs text-left">
                <thead className="bg-stone-50 text-stone-600 border-b border-stone-200">
                  <tr>
                    <th className="py-2.5 px-3 font-semibold">Ingredient</th>
                    <th className="py-2.5 px-3 font-semibold">Recipe Qty</th>
                    <th className="py-2.5 px-3 font-semibold">Purchase Pack</th>
                    <th className="py-2.5 px-3 font-semibold">Pack Cost</th>
                    <th className="py-2.5 px-3 font-semibold text-right">Calculated Cost</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-stone-100">
                  {calculationResult.ingredient_results.map((ing, idx) => (
                    <tr key={idx} className="hover:bg-stone-50/60">
                      <td className="py-2.5 px-3 font-medium text-stone-800">{ing.name}</td>
                      <td className="py-2.5 px-3 text-stone-600">
                        {ing.recipe_quantity} {ing.recipe_unit}
                      </td>
                      <td className="py-2.5 px-3 text-stone-600">
                        {ing.purchase_quantity} {ing.purchase_unit}
                      </td>
                      <td className="py-2.5 px-3 text-stone-600">
                        {formatRupee(ing.purchase_price)}
                      </td>
                      <td className="py-2.5 px-3 text-right font-bold text-forest-900">
                        {formatRupee(ing.cost)}
                      </td>
                    </tr>
                  ))}
                </tbody>
                <tfoot className="border-t-2 border-stone-200 bg-stone-50/50">
                  <tr>
                    <td colSpan={4} className="py-2.5 px-3 font-semibold text-stone-700">
                      Total Ingredients Cost
                    </td>
                    <td className="py-2.5 px-3 text-right font-bold text-forest-900">
                      {formatRupee(calculationResult.total_ingredients_cost)}
                    </td>
                  </tr>
                </tfoot>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
