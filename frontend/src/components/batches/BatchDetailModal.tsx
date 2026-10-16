import React, { useState, useEffect } from 'react';
import { BatchRecordDetailResponse } from '../../types/costing';
import { api } from '../../lib/api';
import { formatRupee, formatPercent } from '../../lib/currency';
import { AuditBreakdownModal } from '../costing/AuditBreakdownModal';
import { Button } from '../common/Button';
import {
  X,
  Calendar,
  Layers,
  TrendingUp,
  FileText,
  Package,
} from 'lucide-react';

interface BatchDetailModalProps {
  isOpen: boolean;
  onClose: () => void;
  batchId: string | null;
  onCloneToWorkspace?: (detail: BatchRecordDetailResponse) => void;
}

export const BatchDetailModal: React.FC<BatchDetailModalProps> = ({
  isOpen,
  onClose,
  batchId,
  onCloneToWorkspace,
}) => {
  const [detail, setDetail] = useState<BatchRecordDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [showAudit, setShowAudit] = useState(false);

  useEffect(() => {
    if (!isOpen || !batchId) return;

    async function loadDetail() {
      setIsLoading(true);
      try {
        const data = await api.getBatch(batchId as string);
        setDetail(data);
      } catch (err) {
        console.error('Failed to load batch detail', err);
      } finally {
        setIsLoading(false);
      }
    }

    loadDetail();
  }, [isOpen, batchId]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 overflow-y-auto bg-stone-900/60 backdrop-blur-sm flex items-center justify-center p-4">
      <div className="bg-white w-full max-w-3xl rounded-xl shadow-2xl border border-stone-200 overflow-hidden flex flex-col max-h-[90vh]">
        {/* Header */}
        <div className="bg-forest-900 text-white p-5 flex items-center justify-between">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-lime-400">
              Historical Batch Record
            </span>
            <h3 className="font-bold text-lg font-serif">
              {detail?.batch_name || 'Loading Batch...'}
            </h3>
            {detail?.created_at && (
              <span className="text-xs text-stone-300 flex items-center gap-1 mt-0.5">
                <Calendar className="w-3.5 h-3.5" />
                {new Date(detail.created_at).toLocaleString()}
              </span>
            )}
          </div>
          <button onClick={onClose} className="text-stone-300 hover:text-white p-1 rounded-md">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-5 overflow-y-auto space-y-5 text-xs sm:text-sm">
          {isLoading || !detail ? (
            <div className="text-center py-10 text-stone-500">Loading batch details...</div>
          ) : (
            <>
              {/* Summary Metrics Grid */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-stone-50 rounded-lg p-3 border border-stone-100">
                  <span className="text-[11px] text-stone-500 block">Total Cost</span>
                  <span className="text-lg font-bold text-stone-900">
                    {formatRupee(detail.total_batch_cost)}
                  </span>
                </div>
                <div className="bg-stone-50 rounded-lg p-3 border border-stone-100">
                  <span className="text-[11px] text-stone-500 block">Sellable Units</span>
                  <span className="text-lg font-bold text-stone-900">
                    {detail.sellable_quantity} {detail.unit_name}
                  </span>
                </div>
                <div className="bg-stone-50 rounded-lg p-3 border border-stone-100">
                  <span className="text-[11px] text-stone-500 block">Unit Cost</span>
                  <span className="text-lg font-bold text-stone-900">
                    {formatRupee(detail.cost_per_sellable_unit)}
                  </span>
                </div>
                <div className="bg-stone-50 rounded-lg p-3 border border-stone-100">
                  <span className="text-[11px] text-stone-500 block">Profit Margin</span>
                  <span className="text-lg font-bold text-emerald-700">
                    {detail.profit_margin_pct ? formatPercent(Number(detail.profit_margin_pct)) : '—'}
                  </span>
                </div>
              </div>

              {/* Profitability Details */}
              {detail.planned_selling_price && (
                <div className="bg-emerald-50 rounded-xl p-4 border border-emerald-200">
                  <div className="flex items-center gap-1.5 font-semibold text-emerald-950 mb-2">
                    <TrendingUp className="w-4 h-4 text-emerald-700" />
                    <span>Financial Performance</span>
                  </div>
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                    <div>
                      <span className="text-stone-500 block">Selling Price:</span>
                      <strong className="text-stone-900 text-sm">
                        {formatRupee(detail.planned_selling_price)}
                      </strong>
                    </div>
                    <div>
                      <span className="text-stone-500 block">Projected Profit:</span>
                      <strong className="text-emerald-800 text-sm">
                        {formatRupee(detail.projected_profit || '0')}
                      </strong>
                    </div>
                    <div>
                      <span className="text-stone-500 block">Markup:</span>
                      <strong className="text-stone-900 text-sm">
                        {detail.calculation_result?.markup_pct
                          ? formatPercent(Number(detail.calculation_result.markup_pct))
                          : '—'}
                      </strong>
                    </div>
                    <div>
                      <span className="text-stone-500 block">Break-Even Units:</span>
                      <strong className="text-stone-900 text-sm">
                        {detail.calculation_result?.break_even_units_to_sell || '0'} units
                      </strong>
                    </div>
                  </div>
                </div>
              )}

              {/* Ingredients Table */}
              <div>
                <h4 className="font-semibold text-stone-900 text-xs sm:text-sm mb-2 flex items-center gap-1.5">
                  <Layers className="w-4 h-4 text-forest-700" />
                  <span>Consumed Ingredients</span>
                </h4>
                <div className="border border-stone-200 rounded-lg overflow-x-auto">
                  <table className="w-full text-xs text-left">
                    <thead className="bg-stone-50 text-stone-600 border-b border-stone-200">
                      <tr>
                        <th className="py-2 px-3 font-semibold">Ingredient</th>
                        <th className="py-2 px-3 font-semibold">Batch Usage</th>
                        <th className="py-2 px-3 font-semibold">Purchase Pack</th>
                        <th className="py-2 px-3 font-semibold text-right">Computed Cost</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                      {detail.calculation_result?.ingredient_results?.map((ing, i) => (
                        <tr key={i}>
                          <td className="py-2 px-3 font-medium text-stone-800">{ing.name}</td>
                          <td className="py-2 px-3 text-stone-600">
                            {ing.recipe_quantity} {ing.recipe_unit}
                          </td>
                          <td className="py-2 px-3 text-stone-600">
                            {ing.purchase_quantity} {ing.purchase_unit} @ {formatRupee(ing.purchase_price)}
                          </td>
                          <td className="py-2 px-3 text-right font-bold text-forest-900">
                            {formatRupee(ing.cost)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Overheads Breakdown */}
              <div>
                <h4 className="font-semibold text-stone-900 text-xs sm:text-sm mb-2 flex items-center gap-1.5">
                  <Package className="w-4 h-4 text-forest-700" />
                  <span>Operational Overheads</span>
                </h4>
                <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs bg-stone-50 p-3 rounded-lg border border-stone-200">
                  <div>
                    <span className="text-stone-500 block">Packaging</span>
                    <strong>{formatRupee(detail.calculation_result?.packaging_cost || '0')}</strong>
                  </div>
                  <div>
                    <span className="text-stone-500 block">Labour</span>
                    <strong>{formatRupee(detail.calculation_result?.labour_cost || '0')}</strong>
                  </div>
                  <div>
                    <span className="text-stone-500 block">Fuel / Gas</span>
                    <strong>{formatRupee(detail.calculation_result?.fuel_cost || '0')}</strong>
                  </div>
                  <div>
                    <span className="text-stone-500 block">Delivery</span>
                    <strong>{formatRupee(detail.calculation_result?.delivery_cost || '0')}</strong>
                  </div>
                  <div>
                    <span className="text-stone-500 block">Other Exps</span>
                    <strong>{formatRupee(detail.calculation_result?.other_expenses || '0')}</strong>
                  </div>
                </div>
              </div>
            </>
          )}
        </div>

        {/* Footer */}
        <div className="bg-stone-50 border-t border-stone-200 p-4 flex justify-between items-center">
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAudit(true)}
            disabled={!detail?.calculation_result?.audit_trail?.length}
          >
            <FileText className="w-4 h-4 mr-1 text-forest-700" />
            Audit Trace ({detail?.calculation_result?.audit_trail?.length || 0})
          </Button>

          <div className="flex items-center gap-2">
            {onCloneToWorkspace && detail && (
              <Button
                variant="primary"
                size="sm"
                onClick={() => {
                  onCloneToWorkspace(detail);
                  onClose();
                }}
                className="bg-forest-900 hover:bg-forest-950 text-white"
              >
                Cost Again in Workspace
              </Button>
            )}
            <Button variant="outline" size="sm" onClick={onClose}>
              Close
            </Button>
          </div>
        </div>
      </div>

      {/* Audit Modal */}
      {detail?.calculation_result && (
        <AuditBreakdownModal
          isOpen={showAudit}
          onClose={() => setShowAudit(false)}
          auditTrail={detail.calculation_result.audit_trail}
          batchName={detail.batch_name}
        />
      )}
    </div>
  );
};

