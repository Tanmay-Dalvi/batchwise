import React, { useState, useEffect } from 'react';
import { CandidateBatchExtraction } from '../../types/ai';
import { BatchCostingInput, IngredientInput } from '../../types/costing';
import { Button } from '../common/Button';
import {
  X,
  AlertTriangle,
  CheckCircle,
  HelpCircle,
  Sparkles,
  ArrowRight,
  Plus,
  Trash2,
} from 'lucide-react';

interface ReviewConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  candidate: CandidateBatchExtraction | null;
  onApply: (costingInput: BatchCostingInput) => void;
}

export const ReviewConfirmModal: React.FC<ReviewConfirmModalProps> = ({
  isOpen,
  onClose,
  candidate,
  onApply,
}) => {
  if (!isOpen || !candidate) return null;

  // Editable local state in staging review
  const [batchName, setBatchName] = useState(candidate.batch_name || 'Extracted Batch');
  const [ingredients, setIngredients] = useState<IngredientInput[]>([]);
  const [packagingCost, setPackagingCost] = useState(candidate.packaging_cost || '0');
  const [labourCost, setLabourCost] = useState(candidate.labour_cost || '0');
  const [fuelCost, setFuelCost] = useState(candidate.fuel_cost || '0');
  const [deliveryCost, setDeliveryCost] = useState(candidate.delivery_cost || '0');
  const [otherExpenses, setOtherExpenses] = useState(candidate.other_expenses || '0');
  const [sellableQuantity, setSellableQuantity] = useState(candidate.sellable_quantity || '1');
  const [unitName, setUnitName] = useState(candidate.yield_unit_name || 'packets');
  const [plannedSellingPrice, setPlannedSellingPrice] = useState(
    candidate.planned_selling_price || ''
  );

  // Sync candidate ingredients to local state on open
  useEffect(() => {
    if (candidate) {
      setBatchName(candidate.batch_name || 'Extracted Batch');
      setPackagingCost(candidate.packaging_cost || '0');
      setLabourCost(candidate.labour_cost || '0');
      setFuelCost(candidate.fuel_cost || '0');
      setDeliveryCost(candidate.delivery_cost || '0');
      setOtherExpenses(candidate.other_expenses || '0');
      setSellableQuantity(candidate.sellable_quantity || '1');
      setUnitName(candidate.yield_unit_name || 'packets');
      setPlannedSellingPrice(candidate.planned_selling_price || '');

      setIngredients(
        candidate.ingredients.map((ing) => ({
          name: ing.name || 'Ingredient',
          recipe_quantity: ing.recipe_quantity || '1',
          recipe_unit: ing.recipe_unit || 'kg',
          purchase_quantity: ing.purchase_quantity || ing.recipe_quantity || '1',
          purchase_unit: ing.purchase_unit || ing.recipe_unit || 'kg',
          purchase_price: ing.purchase_price || '0',
        }))
      );
    }
  }, [candidate]);

  const handleUpdateIngredient = (idx: number, field: keyof IngredientInput, val: string) => {
    const updated = [...ingredients];
    updated[idx] = { ...updated[idx], [field]: val };
    setIngredients(updated);
  };

  const handleRemoveIngredient = (idx: number) => {
    setIngredients(ingredients.filter((_, i) => i !== idx));
  };

  const handleAddIngredient = () => {
    setIngredients([
      ...ingredients,
      {
        name: 'New Item',
        recipe_quantity: '1',
        recipe_unit: 'kg',
        purchase_quantity: '1',
        purchase_unit: 'kg',
        purchase_price: '0',
      },
    ]);
  };

  const handleApply = () => {
    const payload: BatchCostingInput = {
      batch_name: batchName,
      ingredients,
      packaging_cost: packagingCost,
      labour_cost: labourCost,
      fuel_cost: fuelCost,
      delivery_cost: deliveryCost,
      other_expenses: otherExpenses,
      direct_wastage_expense: '0',
      batch_yield: {
        unit_name: unitName,
        sellable_quantity: sellableQuantity,
      },
      planned_selling_price: plannedSellingPrice || null,
      target_margin_pct: '40',
    };
    onApply(payload);
    onClose();
  };

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-3xl rounded-xl shadow-2xl border border-stone-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-forest-900 text-white p-5 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <Sparkles className="w-5 h-5 text-lime-400" />
            <div>
              <h3 className="font-semibold text-lg font-serif">Review AI Extracted Batch</h3>
              <p className="text-xs text-stone-300">
                Gemma 3 1B structured your note. Verify candidate fields before calculation.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-stone-300 hover:text-white p-1 rounded-md"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Modal Body */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs sm:text-sm">
          {/* Raw Note Reference */}
          <div className="bg-stone-50 border border-stone-200 rounded-lg p-3">
            <span className="text-[11px] font-semibold text-stone-500 uppercase tracking-wider block mb-1">
              Original Note
            </span>
            <p className="text-stone-800 italic font-mono text-xs">
              "{candidate.raw_note}"
            </p>
          </div>

          {/* Ambiguity Warnings */}
          {candidate.ambiguities && candidate.ambiguities.length > 0 && (
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 space-y-2">
              <div className="flex items-center gap-2 text-amber-900 font-semibold text-xs">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Ambiguous items require verification:</span>
              </div>
              <ul className="list-disc pl-5 text-xs text-amber-800 space-y-1">
                {candidate.ambiguities.map((a, i) => (
                  <li key={i}>
                    <strong>{a.field_name}:</strong> {a.question} (Detected "{a.raw_text}")
                  </li>
                ))}
              </ul>
            </div>
          )}

          {/* Missing Fields notice */}
          {candidate.missing_fields && candidate.missing_fields.length > 0 && (
            <div className="flex items-center gap-2 text-stone-600 text-xs bg-stone-100 p-2.5 rounded-md">
              <HelpCircle className="w-4 h-4 text-stone-500 shrink-0" />
              <span>
                Missing in note: <strong>{candidate.missing_fields.join(', ')}</strong> (defaults will be set to ₹0)
              </span>
            </div>
          )}

          {/* Candidate Form */}
          <div className="space-y-4">
            <div>
              <label className="text-xs font-semibold text-stone-700 block mb-1">
                Batch Title
              </label>
              <input
                type="text"
                value={batchName}
                onChange={(e) => setBatchName(e.target.value)}
                className="w-full text-xs sm:text-sm px-3 py-1.5 rounded-lg border border-stone-300 bg-white"
              />
            </div>

            {/* Candidate Ingredients */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <label className="text-xs font-semibold text-stone-700">
                  Extracted Ingredients ({ingredients.length})
                </label>
                <button
                  type="button"
                  onClick={handleAddIngredient}
                  className="text-xs text-forest-700 hover:text-forest-900 flex items-center gap-1 font-medium"
                >
                  <Plus className="w-3.5 h-3.5" />
                  Add Item
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
                        placeholder="Ingredient"
                        className="w-full px-2 py-1 rounded border border-stone-300 bg-white text-xs"
                      />
                    </div>
                    <div className="col-span-3 flex gap-1">
                      <input
                        type="number"
                        value={ing.recipe_quantity}
                        onChange={(e) =>
                          handleUpdateIngredient(idx, 'recipe_quantity', e.target.value)
                        }
                        placeholder="Qty"
                        className="w-12 px-1.5 py-1 rounded border border-stone-300 bg-white text-xs"
                      />
                      <input
                        type="text"
                        value={ing.recipe_unit}
                        onChange={(e) =>
                          handleUpdateIngredient(idx, 'recipe_unit', e.target.value)
                        }
                        placeholder="Unit"
                        className="w-12 px-1.5 py-1 rounded border border-stone-300 bg-white text-xs"
                      />
                    </div>
                    <div className="col-span-3 relative">
                      <span className="absolute left-1.5 top-1/2 -translate-y-1/2 text-stone-400 text-xs">
                        ₹
                      </span>
                      <input
                        type="number"
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

            {/* Overheads & Yield Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 pt-2">
              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Packaging (₹)
                </label>
                <input
                  type="number"
                  value={packagingCost}
                  onChange={(e) => setPackagingCost(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Labour (₹)
                </label>
                <input
                  type="number"
                  value={labourCost}
                  onChange={(e) => setLabourCost(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Fuel/Gas (₹)
                </label>
                <input
                  type="number"
                  value={fuelCost}
                  onChange={(e) => setFuelCost(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Delivery (₹)
                </label>
                <input
                  type="number"
                  value={deliveryCost}
                  onChange={(e) => setDeliveryCost(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Sellable Units
                </label>
                <input
                  type="number"
                  value={sellableQuantity}
                  onChange={(e) => setSellableQuantity(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Unit Name
                </label>
                <input
                  type="text"
                  value={unitName}
                  onChange={(e) => setUnitName(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Selling Price (₹)
                </label>
                <input
                  type="number"
                  value={plannedSellingPrice}
                  onChange={(e) => setPlannedSellingPrice(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>

              <div>
                <label className="text-[11px] font-medium text-stone-600 block mb-1">
                  Other Exps (₹)
                </label>
                <input
                  type="number"
                  value={otherExpenses}
                  onChange={(e) => setOtherExpenses(e.target.value)}
                  className="w-full px-2.5 py-1 rounded border border-stone-300 text-xs"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="bg-stone-50 border-t border-stone-200 p-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-1.5 text-stone-500 text-xs">
            <CheckCircle className="w-4 h-4 text-emerald-600" />
            <span>Pure arithmetic performed deterministically on application</span>
          </div>

          <div className="flex items-center gap-2 w-full sm:w-auto">
            <Button variant="outline" size="sm" onClick={onClose} className="flex-1 sm:flex-initial">
              Discard
            </Button>
            <Button
              variant="primary"
              size="sm"
              onClick={handleApply}
              className="flex-1 sm:flex-initial bg-forest-900 hover:bg-forest-950 text-white"
            >
              <span>Apply to Workspace</span>
              <ArrowRight className="w-4 h-4 ml-1 text-lime-400" />
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
};

