import React, { useState, useEffect } from 'react';
import { RecipeCreate, RecipeResponse, RecipeIngredientCreate } from '../../types/recipe';
import { api, ApiError } from '../../lib/api';
import { Button } from '../common/Button';
import { Input } from '../common/Input';
import { X, Plus, Trash2, Layers, AlertCircle } from 'lucide-react';

interface RecipeModalProps {
  isOpen: boolean;
  onClose: () => void;
  recipe?: RecipeResponse | null;
  onSaved: (recipe: RecipeResponse) => void;
}

const COMMON_UNITS = ['kg', 'g', 'L', 'ml', 'units', 'dozens', 'packets'];

export const RecipeModal: React.FC<RecipeModalProps> = ({
  isOpen,
  onClose,
  recipe,
  onSaved,
}) => {
  if (!isOpen) return null;

  const [name, setName] = useState(recipe?.name || '');
  const [description, setDescription] = useState(recipe?.description || '');
  const [yieldUnit, setYieldUnit] = useState(recipe?.yield_unit || 'packets');
  const [packagingCost, setPackagingCost] = useState(recipe?.default_packaging_cost || '0');
  const [labourCost, setLabourCost] = useState(recipe?.default_labour_cost || '0');
  const [fuelCost, setFuelCost] = useState(recipe?.default_fuel_cost || '0');
  const [deliveryCost, setDeliveryCost] = useState(recipe?.default_delivery_cost || '0');
  const [otherExpenses, setOtherExpenses] = useState(recipe?.default_other_expenses || '0');

  const [ingredients, setIngredients] = useState<RecipeIngredientCreate[]>(
    recipe?.ingredients?.length
      ? recipe.ingredients.map((i) => ({
          name: i.name,
          recipe_quantity: i.recipe_quantity,
          recipe_unit: i.recipe_unit,
          purchase_quantity: i.purchase_quantity || i.recipe_quantity,
          purchase_unit: i.purchase_unit || i.recipe_unit,
          purchase_price: i.purchase_price,
        }))
      : [
          {
            name: '',
            recipe_quantity: '1',
            recipe_unit: 'kg',
            purchase_quantity: '1',
            purchase_unit: 'kg',
            purchase_price: '0',
          },
        ]
  );

  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (recipe) {
      setName(recipe.name);
      setDescription(recipe.description || '');
      setYieldUnit(recipe.yield_unit);
      setPackagingCost(recipe.default_packaging_cost);
      setLabourCost(recipe.default_labour_cost);
      setFuelCost(recipe.default_fuel_cost);
      setDeliveryCost(recipe.default_delivery_cost);
      setOtherExpenses(recipe.default_other_expenses);
      setIngredients(
        recipe.ingredients.map((i) => ({
          name: i.name,
          recipe_quantity: i.recipe_quantity,
          recipe_unit: i.recipe_unit,
          purchase_quantity: i.purchase_quantity,
          purchase_unit: i.purchase_unit,
          purchase_price: i.purchase_price,
        }))
      );
    } else {
      setName('');
      setDescription('');
      setYieldUnit('packets');
      setPackagingCost('0');
      setLabourCost('0');
      setFuelCost('0');
      setDeliveryCost('0');
      setOtherExpenses('0');
      setIngredients([
        {
          name: '',
          recipe_quantity: '1',
          recipe_unit: 'kg',
          purchase_quantity: '1',
          purchase_unit: 'kg',
          purchase_price: '0',
        },
      ]);
    }
  }, [recipe, isOpen]);

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

  const handleUpdateIngredient = (idx: number, field: keyof RecipeIngredientCreate, val: string) => {
    const updated = [...ingredients];
    updated[idx] = { ...updated[idx], [field]: val };
    if (field === 'recipe_unit' && (!updated[idx].purchase_unit || updated[idx].purchase_unit === '')) {
      updated[idx].purchase_unit = val;
    }
    setIngredients(updated);
  };

  const handleRemoveIngredient = (idx: number) => {
    if (ingredients.length <= 1) {
      setError('Recipe must have at least one ingredient.');
      return;
    }
    setIngredients(ingredients.filter((_, i) => i !== idx));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim()) {
      setError('Recipe name is required.');
      return;
    }

    setError(null);
    setIsSaving(true);

    const payload: RecipeCreate = {
      name: name.trim(),
      description: description.trim() || null,
      yield_unit: yieldUnit.trim() || 'packets',
      default_packaging_cost: packagingCost || '0',
      default_labour_cost: labourCost || '0',
      default_fuel_cost: fuelCost || '0',
      default_delivery_cost: deliveryCost || '0',
      default_other_expenses: otherExpenses || '0',
      ingredients: ingredients.map((i) => ({
        name: i.name.trim() || 'Ingredient',
        recipe_quantity: i.recipe_quantity || '1',
        recipe_unit: i.recipe_unit || 'kg',
        purchase_quantity: i.purchase_quantity || i.recipe_quantity || '1',
        purchase_unit: i.purchase_unit || i.recipe_unit || 'kg',
        purchase_price: i.purchase_price || '0',
      })),
    };

    try {
      let saved: RecipeResponse;
      if (recipe) {
        saved = await api.updateRecipe(recipe.id, payload);
      } else {
        saved = await api.createRecipe(payload);
      }
      onSaved(saved);
      onClose();
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError('Failed to save recipe. Please check your connection.');
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-2xl rounded-xl shadow-2xl border border-stone-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-forest-900 text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="w-5 h-5 text-lime-400" />
            <h3 className="font-semibold text-lg font-serif">
              {recipe ? 'Edit Recipe Template' : 'New Recipe Template'}
            </h3>
          </div>
          <button onClick={onClose} className="text-stone-300 hover:text-white p-1 rounded-md">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Form Body */}
        <form onSubmit={handleSubmit} className="p-5 overflow-y-auto space-y-4 text-xs sm:text-sm">
          {error && (
            <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-800 text-xs">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            <div className="sm:col-span-2">
              <Input
                label="Recipe Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="e.g. Samosa Standard Batch"
                required
              />
            </div>
            <div>
              <Input
                label="Yield Unit Name"
                value={yieldUnit}
                onChange={(e) => setYieldUnit(e.target.value)}
                placeholder="packets, boxes"
                required
              />
            </div>
          </div>

          <Input
            label="Description (Optional)"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Standard preparation notes, ingredients ratio, etc."
          />

          {/* Ingredients list */}
          <div>
            <div className="flex justify-between items-center mb-2">
              <span className="font-semibold text-stone-700 text-xs">
                Ingredients ({ingredients.length})
              </span>
              <button
                type="button"
                onClick={handleAddIngredient}
                className="text-xs text-forest-700 hover:text-forest-900 flex items-center gap-1 font-medium"
              >
                <Plus className="w-3.5 h-3.5" />
                Add Ingredient
              </button>
            </div>

            <div className="space-y-2">
              {ingredients.map((ing, idx) => (
                <div
                  key={idx}
                  className="p-2.5 bg-stone-50 rounded-lg border border-stone-200 grid grid-cols-12 gap-2 items-center text-xs"
                >
                  <div className="col-span-5">
                    <input
                      type="text"
                      value={ing.name}
                      onChange={(e) => handleUpdateIngredient(idx, 'name', e.target.value)}
                      placeholder="Ingredient name"
                      className="w-full px-2 py-1 rounded border border-stone-300 bg-white text-xs"
                    />
                  </div>
                  <div className="col-span-3 flex gap-1">
                    <input
                      type="number"
                      step="any"
                      value={ing.recipe_quantity}
                      onChange={(e) =>
                        handleUpdateIngredient(idx, 'recipe_quantity', e.target.value)
                      }
                      placeholder="Qty"
                      className="w-12 px-1.5 py-1 rounded border border-stone-300 bg-white text-xs"
                    />
                    <select
                      value={ing.recipe_unit}
                      onChange={(e) =>
                        handleUpdateIngredient(idx, 'recipe_unit', e.target.value)
                      }
                      className="flex-1 px-1 py-1 rounded border border-stone-300 bg-white text-xs"
                    >
                      {COMMON_UNITS.map((u) => (
                        <option key={u} value={u}>
                          {u}
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-span-3 relative">
                    <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-stone-400 text-xs">
                      ₹
                    </span>
                    <input
                      type="number"
                      step="any"
                      value={ing.purchase_price}
                      onChange={(e) =>
                        handleUpdateIngredient(idx, 'purchase_price', e.target.value)
                      }
                      placeholder="Price"
                      className="w-full pl-4 pr-1.5 py-1 rounded border border-stone-300 bg-white text-xs"
                    />
                  </div>
                  <div className="col-span-1 flex justify-end">
                    <button
                      type="button"
                      onClick={() => handleRemoveIngredient(idx)}
                      className="text-stone-400 hover:text-rose-600"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Default Overheads */}
          <div>
            <span className="font-semibold text-stone-700 text-xs block mb-2">
              Default Overhead Estimates (₹)
            </span>
            <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
              <Input
                label="Packaging"
                type="number"
                value={packagingCost}
                onChange={(e) => setPackagingCost(e.target.value)}
              />
              <Input
                label="Labour"
                type="number"
                value={labourCost}
                onChange={(e) => setLabourCost(e.target.value)}
              />
              <Input
                label="Fuel"
                type="number"
                value={fuelCost}
                onChange={(e) => setFuelCost(e.target.value)}
              />
              <Input
                label="Delivery"
                type="number"
                value={deliveryCost}
                onChange={(e) => setDeliveryCost(e.target.value)}
              />
              <Input
                label="Other"
                type="number"
                value={otherExpenses}
                onChange={(e) => setOtherExpenses(e.target.value)}
              />
            </div>
          </div>

          {/* Modal Footer */}
          <div className="pt-3 border-t border-stone-200 flex justify-end gap-2">
            <Button variant="outline" size="sm" type="button" onClick={onClose}>
              Cancel
            </Button>
            <Button
              variant="primary"
              size="sm"
              type="submit"
              disabled={isSaving}
              className="bg-forest-900 hover:bg-forest-950 text-white"
            >
              {isSaving ? 'Saving...' : recipe ? 'Update Recipe' : 'Create Recipe'}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
};

