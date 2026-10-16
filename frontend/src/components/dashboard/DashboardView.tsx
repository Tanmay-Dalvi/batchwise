import React, { useState, useEffect } from 'react';
import { BatchRecordSummary } from '../../types/costing';
import { RecipeResponse } from '../../types/recipe';
import { api } from '../../lib/api';
import { formatRupee, formatPercent } from '../../lib/currency';
import { Button } from '../common/Button';
import {
  Layers,
  Sparkles,
  BookmarkPlus,
  ArrowRight,
  ChevronRight,
  Calculator,
} from 'lucide-react';

interface DashboardViewProps {
  onNavigateToCosting: () => void;
  onNavigateToAiNotes: () => void;
  onNavigateToRecipes: () => void;
  onNavigateToHistory: () => void;
  onCostRecipe: (recipe: RecipeResponse) => void;
}

export const DashboardView: React.FC<DashboardViewProps> = ({
  onNavigateToCosting,
  onNavigateToAiNotes,
  onNavigateToRecipes,
  onNavigateToHistory,
  onCostRecipe,
}) => {
  const [recentBatches, setRecentBatches] = useState<BatchRecordSummary[]>([]);
  const [recipes, setRecipes] = useState<RecipeResponse[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadDashboardData() {
      setIsLoading(true);
      try {
        const [batchList, recipeList] = await Promise.all([
          api.listBatches().catch(() => []),
          api.listRecipes().catch(() => []),
        ]);
        setRecentBatches(batchList);
        setRecipes(recipeList);
      } catch (err) {
        console.error('Error loading dashboard data', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboardData();
  }, []);

  // Compute actual summary metrics
  const totalBatches = recentBatches.length;
  const totalCostNumber = recentBatches.reduce(
    (acc, b) => acc + (Number(b.total_batch_cost) || 0),
    0
  );
  const margins = recentBatches
    .map((b) => (b.profit_margin_pct ? Number(b.profit_margin_pct) : null))
    .filter((m): m is number => m !== null);
  const avgMargin =
    margins.length > 0 ? margins.reduce((acc, m) => acc + m, 0) / margins.length : null;

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Hero Card */}
      <div className="bg-forest-900 text-stone-100 rounded-2xl p-6 sm:p-8 shadow-md relative overflow-hidden">
        {/* Subtle decorative background watermark */}
        <div className="absolute right-0 bottom-0 translate-x-8 translate-y-8 opacity-5 pointer-events-none">
          <Layers className="w-80 h-80 text-white" />
        </div>

        <div className="relative z-10 max-w-2xl space-y-4">
          <div className="inline-flex items-center gap-2 px-2.5 py-1 rounded-full bg-forest-800 border border-forest-700 text-lime-400 text-xs font-semibold uppercase tracking-wider">
            <span className="w-2 h-2 rounded-full bg-lime-400 animate-pulse"></span>
            <span>Batchwise Local-First Engine</span>
          </div>

          <h1 className="text-2xl sm:text-4xl font-serif font-bold text-white tracking-tight leading-tight">
            Every batch. Every cost. <br className="hidden sm:inline" />
            <span className="text-lime-400">Every rupee.</span>
          </h1>

          <p className="text-stone-300 text-xs sm:text-sm leading-relaxed">
            Engineered for Indian home-based snack sellers, bakers, and tiffin providers.
            Know your exact ingredient costs, overheads, wastage, break-even price, and true margins.
          </p>

          <div className="pt-2 flex flex-wrap gap-3">
            <Button
              variant="primary"
              size="md"
              onClick={onNavigateToCosting}
              className="bg-lime-500 hover:bg-lime-600 text-forest-950 font-bold px-5"
            >
              <Layers className="w-4 h-4 mr-1.5" />
              <span>Cost a New Batch</span>
            </Button>
            <Button
              variant="outline"
              size="md"
              onClick={onNavigateToAiNotes}
              className="border-stone-600 text-stone-200 hover:text-white hover:bg-forest-800"
            >
              <Sparkles className="w-4 h-4 mr-1.5 text-lime-400" />
              <span>Parse Messy Notes</span>
            </Button>
          </div>
        </div>
      </div>

      {/* Brand Identity / Meaning Card */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm">
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
          <div className="border-b sm:border-b-0 sm:border-r border-stone-100 pb-3 sm:pb-0 sm:pr-4">
            <h4 className="font-bold text-stone-900 font-serif text-sm mb-1 flex items-center gap-1.5">
              <span className="text-forest-700">1.</span> What is a "Batch"?
            </h4>
            <p className="text-stone-600">
              One real production run: snacks, bread, sweets, or meals consuming raw ingredients, fuel, packaging, and labour.
            </p>
          </div>

          <div className="border-b sm:border-b-0 sm:border-r border-stone-100 pb-3 sm:pb-0 sm:pr-4">
            <h4 className="font-bold text-stone-900 font-serif text-sm mb-1 flex items-center gap-1.5">
              <span className="text-forest-700">2.</span> Why "Wise"?
            </h4>
            <p className="text-stone-600">
              Making data-driven, mathematically proven decisions instead of guessing wholesale prices or absorbing silent losses.
            </p>
          </div>

          <div>
            <h4 className="font-bold text-stone-900 font-serif text-sm mb-1 flex items-center gap-1.5">
              <span className="text-forest-700">3.</span> Pure Deterministic Math
            </h4>
            <p className="text-stone-600">
              Zero floating-point rounding errors and zero AI arithmetic. Python Decimal math guarantees 100% precision.
            </p>
          </div>
        </div>
      </div>

      {/* Summary Metrics (when available) */}
      {totalBatches > 0 && (
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div className="bg-white rounded-xl border border-stone-200 p-4 shadow-sm">
            <span className="text-xs font-medium text-stone-500 block">Total Batches Recorded</span>
            <span className="text-2xl font-bold font-serif text-stone-900">{totalBatches}</span>
            <span className="text-[11px] text-stone-500 block mt-1">Saved in local SQLite database</span>
          </div>

          <div className="bg-white rounded-xl border border-stone-200 p-4 shadow-sm">
            <span className="text-xs font-medium text-stone-500 block">Total Production Costed</span>
            <span className="text-2xl font-bold font-serif text-stone-900">
              {formatRupee(totalCostNumber.toFixed(2))}
            </span>
            <span className="text-[11px] text-stone-500 block mt-1">Cumulative material & overhead value</span>
          </div>

          <div className="bg-white rounded-xl border border-stone-200 p-4 shadow-sm">
            <span className="text-xs font-medium text-stone-500 block">Average Profit Margin</span>
            <span className="text-2xl font-bold font-serif text-emerald-700">
              {avgMargin !== null ? formatPercent(avgMargin) : '—'}
            </span>
            <span className="text-[11px] text-stone-500 block mt-1">Across all priced batches</span>
          </div>
        </div>
      )}

      {/* Quick Navigation Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <button
          type="button"
          onClick={onNavigateToCosting}
          className="text-left bg-white rounded-xl border border-stone-200 p-5 shadow-sm hover:border-forest-400 hover:shadow-md transition-all duration-200 group"
        >
          <div className="p-2.5 bg-forest-50 text-forest-800 rounded-lg w-fit mb-3 group-hover:bg-forest-800 group-hover:text-white transition-colors">
            <Layers className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-stone-900 text-sm font-serif mb-1">
            Batch Costing Workspace
          </h3>
          <p className="text-xs text-stone-500 mb-3">
            Enter recipe ingredients, pack purchase costs, and overheads to calculate unit cost and break-even price.
          </p>
          <div className="flex items-center text-xs font-semibold text-forest-700 group-hover:text-forest-900">
            <span>Open workspace</span>
            <ChevronRight className="w-4 h-4 ml-0.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </button>

        <button
          type="button"
          onClick={onNavigateToAiNotes}
          className="text-left bg-white rounded-xl border border-stone-200 p-5 shadow-sm hover:border-forest-400 hover:shadow-md transition-all duration-200 group"
        >
          <div className="p-2.5 bg-lime-100 text-forest-900 rounded-lg w-fit mb-3 group-hover:bg-forest-800 group-hover:text-white transition-colors">
            <Sparkles className="w-5 h-5 text-forest-800 group-hover:text-lime-400" />
          </div>
          <h3 className="font-semibold text-stone-900 text-sm font-serif mb-1">
            Local AI Note Parser
          </h3>
          <p className="text-xs text-stone-500 mb-3">
            Paste quick vendor bills or raw notes. Gemma 3 1B turns messy text into structured inputs for review.
          </p>
          <div className="flex items-center text-xs font-semibold text-forest-700 group-hover:text-forest-900">
            <span>Parse notes</span>
            <ChevronRight className="w-4 h-4 ml-0.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </button>

        <button
          type="button"
          onClick={onNavigateToRecipes}
          className="text-left bg-white rounded-xl border border-stone-200 p-5 shadow-sm hover:border-forest-400 hover:shadow-md transition-all duration-200 group"
        >
          <div className="p-2.5 bg-stone-100 text-stone-800 rounded-lg w-fit mb-3 group-hover:bg-forest-800 group-hover:text-white transition-colors">
            <BookmarkPlus className="w-5 h-5" />
          </div>
          <h3 className="font-semibold text-stone-900 text-sm font-serif mb-1">
            Recipe Templates ({recipes.length})
          </h3>
          <p className="text-xs text-stone-500 mb-3">
            Save master formulas for signature sweets, cakes, and tiffin boxes to cost future batches in seconds.
          </p>
          <div className="flex items-center text-xs font-semibold text-forest-700 group-hover:text-forest-900">
            <span>Manage recipes</span>
            <ChevronRight className="w-4 h-4 ml-0.5 group-hover:translate-x-1 transition-transform" />
          </div>
        </button>
      </div>

      {/* Recent Batches Section */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm space-y-4">
        <div className="flex justify-between items-center">
          <div>
            <h3 className="font-semibold text-stone-900 text-base font-serif">
              Recent Production Batches
            </h3>
            <p className="text-xs text-stone-500">Your latest recorded batches in SQLite</p>
          </div>
          {totalBatches > 0 && (
            <button
              onClick={onNavigateToHistory}
              className="text-xs font-semibold text-forest-700 hover:text-forest-900 flex items-center gap-1"
            >
              <span>View all ({totalBatches})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          )}
        </div>

        {isLoading ? (
          <div className="text-center py-6 text-xs text-stone-500">
            Loading your batches & recipes...
          </div>
        ) : totalBatches === 0 ? (
          <div className="bg-stone-50 rounded-lg p-6 text-center border border-dashed border-stone-200">
            <p className="text-xs sm:text-sm text-stone-600 mb-2">
              No batches recorded yet. Try costing a batch with our canonical example:
            </p>
            <p className="text-xs text-stone-500 italic mb-3">
              "5 kg besan (₹600), 1 L oil (₹180), ₹80 packaging, 75 packets @ ₹25"
            </p>
            <Button variant="primary" size="sm" onClick={onNavigateToCosting}>
              Try Canonical Example
            </Button>
          </div>
        ) : (
          <div className="divide-y divide-stone-100">
            {recentBatches.slice(0, 3).map((batch) => (
              <div
                key={batch.id}
                className="py-3 flex items-center justify-between gap-4 text-xs hover:bg-stone-50/50 px-2 rounded transition-colors"
              >
                <div>
                  <h4 className="font-semibold text-stone-900 text-sm">{batch.batch_name}</h4>
                  <span className="text-stone-500">
                    {new Date(batch.created_at).toLocaleDateString()} • {batch.sellable_quantity}{' '}
                    {batch.unit_name}
                  </span>
                </div>

                <div className="flex items-center gap-4">
                  <div className="text-right">
                    <span className="text-stone-500 block">Total Cost</span>
                    <strong className="text-stone-900">{formatRupee(batch.total_batch_cost)}</strong>
                  </div>
                  {batch.profit_margin_pct && (
                    <span className="text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded border border-emerald-100">
                      {formatPercent(Number(batch.profit_margin_pct))}
                    </span>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Saved Recipes Quick Row (if available) */}
      {!isLoading && recipes.length > 0 && (
        <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm space-y-3">
          <div className="flex justify-between items-center">
            <h3 className="font-semibold text-stone-900 text-base font-serif">
              Saved Recipes Quick-Cost
            </h3>
            <button
              onClick={onNavigateToRecipes}
              className="text-xs font-semibold text-forest-700 hover:text-forest-900 flex items-center gap-1"
            >
              <span>Manage recipes ({recipes.length})</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {recipes.slice(0, 2).map((recipe) => (
              <div
                key={recipe.id}
                className="p-3 bg-stone-50 rounded-lg border border-stone-200 flex items-center justify-between"
              >
                <div>
                  <h4 className="font-medium text-stone-900 text-xs sm:text-sm">{recipe.name}</h4>
                  <span className="text-[11px] text-stone-500">
                    {recipe.ingredients.length} ingredients • {recipe.yield_unit}
                  </span>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onCostRecipe(recipe)}
                  className="text-xs"
                >
                  <Calculator className="w-3 h-3 mr-1 text-forest-700" />
                  <span>Cost Batch</span>
                </Button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
