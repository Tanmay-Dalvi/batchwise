import React, { useState } from 'react';
import { BatchCalculationResult } from '../../types/costing';
import { formatRupee, formatPercent } from '../../lib/currency';
import { AuditBreakdownModal } from './AuditBreakdownModal';
import {
  DollarSign,
  TrendingUp,
  HelpCircle,
  FileText,
  AlertCircle,
  CheckCircle,
} from 'lucide-react';
import { Button } from '../common/Button';

interface CostSummaryCardProps {
  result: BatchCalculationResult;
  onSaveBatch?: () => void;
  isSaving?: boolean;
}

export const CostSummaryCard: React.FC<CostSummaryCardProps> = ({
  result,
  onSaveBatch,
  isSaving = false,
}) => {
  const [showAudit, setShowAudit] = useState(false);
  const [showFormulaHelper, setShowFormulaHelper] = useState(false);

  const hasSellingPrice = Boolean(result.planned_selling_price && Number(result.planned_selling_price) > 0);
  const isProfitable = result.projected_profit ? Number(result.projected_profit) > 0 : false;
  const profitMarginNum = result.profit_margin_pct ? Number(result.profit_margin_pct) : 0;

  return (
    <div className="bg-white rounded-xl border border-stone-200 shadow-sm overflow-hidden transition-all duration-200">
      {/* Top Banner */}
      <div className="bg-forest-900 text-stone-100 p-5 sm:p-6 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <span className="text-xs uppercase tracking-wider font-semibold text-lime-400">
            Calculation Results
          </span>
          <h3 className="text-xl sm:text-2xl font-bold font-serif text-white tracking-tight">
            {result.batch_name || 'Production Batch'}
          </h3>
          <p className="text-xs sm:text-sm text-stone-300 mt-0.5">
            Yield: <strong className="text-white">{result.sellable_quantity} {result.unit_name}</strong>
            {result.gross_quantity && result.scrap_quantity && Number(result.scrap_quantity) > 0 && (
              <span className="text-amber-300 ml-2">
                ({result.scrap_quantity} {result.unit_name} scrap accounted for)
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAudit(true)}
            className="border-stone-600 text-stone-200 hover:text-white hover:bg-forest-800"
          >
            <FileText className="w-4 h-4 mr-1.5 text-lime-400" />
            Audit Trail ({result.audit_trail?.length || 0})
          </Button>
          {onSaveBatch && (
            <Button
              variant="primary"
              size="sm"
              onClick={onSaveBatch}
              disabled={isSaving}
              className="bg-lime-500 hover:bg-lime-600 text-forest-950 font-semibold"
            >
              {isSaving ? 'Saving...' : 'Save Batch'}
            </Button>
          )}
        </div>
      </div>

      <div className="p-5 sm:p-6 space-y-6">
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-stone-50 rounded-lg p-4 border border-stone-100">
            <span className="text-xs font-medium text-stone-500 block mb-1">Total Batch Cost</span>
            <div className="text-xl sm:text-2xl font-bold text-stone-900">
              {formatRupee(result.total_batch_cost)}
            </div>
            <span className="text-[11px] text-stone-500 mt-1 block">
              Ingredients: {formatRupee(result.total_ingredients_cost)}
            </span>
          </div>

          <div className="bg-stone-50 rounded-lg p-4 border border-stone-100">
            <span className="text-xs font-medium text-stone-500 block mb-1">Cost Per Unit</span>
            <div className="text-xl sm:text-2xl font-bold text-stone-900">
              {formatRupee(result.cost_per_sellable_unit)}
            </div>
            <span className="text-[11px] text-stone-500 mt-1 block">
              Per sellable {result.unit_name}
            </span>
          </div>

          <div className="bg-stone-50 rounded-lg p-4 border border-stone-100">
            <span className="text-xs font-medium text-stone-500 block mb-1">Break-Even Price</span>
            <div className="text-xl sm:text-2xl font-bold text-stone-900">
              {formatRupee(result.break_even_price_per_unit)}
            </div>
            <span className="text-[11px] text-stone-500 mt-1 block">
              Minimum zero-profit price
            </span>
          </div>

          <div className="bg-stone-50 rounded-lg p-4 border border-stone-100">
            <span className="text-xs font-medium text-stone-500 block mb-1">Overhead Total</span>
            <div className="text-xl sm:text-2xl font-bold text-stone-900">
              {formatRupee(result.total_overheads)}
            </div>
            <span className="text-[11px] text-stone-500 mt-1 block">
              Fuel, labour, packaging, etc.
            </span>
          </div>
        </div>

        {/* Profitability Panel (when selling price is set) */}
        {hasSellingPrice ? (
          <div
            className={`rounded-xl p-5 border ${
              isProfitable
                ? 'bg-emerald-50/70 border-emerald-200'
                : 'bg-rose-50/70 border-rose-200'
            }`}
          >
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-2">
                {isProfitable ? (
                  <CheckCircle className="w-5 h-5 text-emerald-600" />
                ) : (
                  <AlertCircle className="w-5 h-5 text-rose-600" />
                )}
                <h4 className="font-semibold text-stone-900">
                  {isProfitable ? 'Projected Profitability' : 'Unprofitable Pricing Warning'}
                </h4>
              </div>
              <button
                type="button"
                onClick={() => setShowFormulaHelper(!showFormulaHelper)}
                className="text-xs font-medium text-forest-700 hover:text-forest-900 flex items-center gap-1"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                Margin vs Markup explained
              </button>
            </div>

            {/* Formula Helper Collapsible */}
            {showFormulaHelper && (
              <div className="mb-4 p-3 bg-white/90 rounded-lg border border-stone-200 text-xs text-stone-700 space-y-1.5">
                <p>
                  <strong>Profit Margin (%):</strong> Calculated as{' '}
                  <code className="bg-stone-100 px-1 py-0.5 rounded text-forest-800">
                    (Profit / Revenue) × 100
                  </code>
                  . Represents how much of every rupee collected is profit.
                </p>
                <p>
                  <strong>Markup (%):</strong> Calculated as{' '}
                  <code className="bg-stone-100 px-1 py-0.5 rounded text-forest-800">
                    (Profit / Cost) × 100
                  </code>
                  . Represents how much is added on top of your production cost.
                </p>
                <p className="text-stone-500 italic text-[11px]">
                  Batchwise keeps these transparent so you never miscalculate wholesale or retail prices.
                </p>
              </div>
            )}

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div>
                <span className="text-xs text-stone-500 block">Selling Price</span>
                <span className="text-lg font-bold text-stone-900">
                  {formatRupee(result.planned_selling_price || '0')}
                </span>
                <span className="text-[11px] text-stone-500 block">per {result.unit_name}</span>
              </div>

              <div>
                <span className="text-xs text-stone-500 block">Projected Revenue</span>
                <span className="text-lg font-bold text-stone-900">
                  {formatRupee(result.projected_revenue || '0')}
                </span>
                <span className="text-[11px] text-stone-500 block">
                  {result.sellable_quantity} units sold
                </span>
              </div>

              <div>
                <span className="text-xs text-stone-500 block">Net Profit</span>
                <span
                  className={`text-lg font-bold ${
                    isProfitable ? 'text-emerald-700' : 'text-rose-700'
                  }`}
                >
                  {formatRupee(result.projected_profit || '0')}
                </span>
                <span className="text-[11px] text-stone-500 block">
                  {formatRupee(result.profit_per_unit || '0')} / unit
                </span>
              </div>

              <div>
                <span className="text-xs text-stone-500 block">Margin vs Markup</span>
                <div className="flex items-baseline gap-2">
                  <span
                    className={`text-lg font-bold ${
                      isProfitable ? 'text-emerald-700' : 'text-rose-700'
                    }`}
                  >
                    {formatPercent(profitMarginNum)}
                  </span>
                  <span className="text-xs text-stone-500">
                    ({formatPercent(result.markup_pct ? Number(result.markup_pct) : 0)} markup)
                  </span>
                </div>
                <span className="text-[11px] text-stone-500 block">
                  Break-even: {result.break_even_units_to_sell || '0'} units
                </span>
              </div>
            </div>
          </div>
        ) : (
          <div className="bg-stone-50 rounded-xl p-4 border border-dashed border-stone-200 text-stone-600 text-sm flex items-center justify-between">
            <div className="flex items-center gap-2">
              <DollarSign className="w-4 h-4 text-forest-600" />
              <span>Enter a planned selling price above to calculate profit, margin, and revenue.</span>
            </div>
          </div>
        )}

        {/* Target Margin Recommendation (if provided) */}
        {result.target_margin_selling_price && (
          <div className="bg-lime-50 rounded-xl p-4 border border-lime-200">
            <div className="flex items-center justify-between mb-2">
              <div className="flex items-center gap-1.5 text-lime-900 font-semibold text-sm">
                <TrendingUp className="w-4 h-4 text-lime-700" />
                <span>Target Margin Recommendation ({formatPercent(Number(result.target_margin_pct))} Margin)</span>
              </div>
              <span className="text-xs bg-lime-200 text-lime-900 px-2 py-0.5 rounded-full font-medium">
                Goal: {result.target_margin_pct}%
              </span>
            </div>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 text-sm">
              <div>
                <span className="text-xs text-lime-800 block">Recommended Price:</span>
                <strong className="text-base text-forest-950 font-bold">
                  {formatRupee(result.target_margin_selling_price)}
                </strong>
                <span className="text-[11px] text-lime-700 block">per {result.unit_name}</span>
              </div>
              <div>
                <span className="text-xs text-lime-800 block">Profit at Target:</span>
                <strong className="text-base text-forest-950 font-bold">
                  {formatRupee(result.target_margin_profit_per_unit || '0')}
                </strong>
                <span className="text-[11px] text-lime-700 block">per {result.unit_name}</span>
              </div>
              <div>
                <span className="text-xs text-lime-800 block">Equivalent Markup:</span>
                <strong className="text-base text-forest-950 font-bold">
                  {formatPercent(Number(result.target_margin_markup_pct || '0'))}
                </strong>
                <span className="text-[11px] text-lime-700 block">on unit cost</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Audit Modal */}
      <AuditBreakdownModal
        isOpen={showAudit}
        onClose={() => setShowAudit(false)}
        auditTrail={result.audit_trail}
        batchName={result.batch_name}
      />
    </div>
  );
};
