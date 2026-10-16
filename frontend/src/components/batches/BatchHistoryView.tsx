import React, { useState, useEffect } from 'react';
import { BatchRecordSummary, BatchRecordDetailResponse } from '../../types/costing';
import { api } from '../../lib/api';
import { formatRupee, formatPercent } from '../../lib/currency';
import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { BatchDetailModal } from './BatchDetailModal';
import {
  History,
  Search,
  Eye,
  Trash2,
  Calendar,
  Layers,
} from 'lucide-react';

interface BatchHistoryViewProps {
  onCostNewBatch: () => void;
  onCloneToWorkspace?: (detail: BatchRecordDetailResponse) => void;
}

export const BatchHistoryView: React.FC<BatchHistoryViewProps> = ({
  onCostNewBatch,
  onCloneToWorkspace,
}) => {
  const [batches, setBatches] = useState<BatchRecordSummary[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Detail Modal
  const [selectedBatchId, setSelectedBatchId] = useState<string | null>(null);

  // Delete Dialog
  const [batchToDelete, setBatchToDelete] = useState<BatchRecordSummary | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchBatches = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listBatches();
      setBatches(data);
    } catch (err) {
      setError('Failed to load batch records. Please check your backend connection.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchBatches();
  }, []);

  const handleDelete = async () => {
    if (!batchToDelete) return;
    setIsDeleting(true);
    try {
      await api.deleteBatch(batchToDelete.id);
      setBatches((prev) => prev.filter((b) => b.id !== batchToDelete.id));
      setBatchToDelete(null);
    } catch (err) {
      console.error('Failed to delete batch', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const filtered = batches.filter((b) =>
    b.batch_name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-forest-700">
            Production Records
          </span>
          <h2 className="text-xl sm:text-2xl font-bold font-serif text-stone-900">
            Batch Costing History
          </h2>
          <p className="text-xs sm:text-sm text-stone-500">
            Audit your historical production runs, costs, and profit margins over time.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={onCostNewBatch}
          className="bg-forest-900 hover:bg-forest-950 text-white font-medium"
        >
          <Layers className="w-4 h-4 mr-1.5 text-lime-400" />
          <span>Cost New Batch</span>
        </Button>
      </div>

      {/* Search Input */}
      <div className="relative">
        <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search batches by name..."
          className="w-full pl-9 pr-4 py-2 text-xs sm:text-sm bg-white rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-forest-600"
        />
      </div>

      {/* Batch Cards / Table */}
      {isLoading ? (
        <div className="text-center py-12 text-stone-500 text-sm">Loading batch history...</div>
      ) : error ? (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm text-center">
          {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-stone-300 p-10 text-center space-y-3">
          <History className="w-10 h-10 text-stone-400 mx-auto" />
          <h3 className="font-semibold text-stone-800 text-base">No batch history yet</h3>
          <p className="text-xs sm:text-sm text-stone-500 max-w-sm mx-auto">
            {search
              ? 'No batches match your search.'
              : 'Calculate and save production batches in the workspace to track your true costs and margins.'}
          </p>
          {!search && (
            <Button variant="outline" size="sm" onClick={onCostNewBatch}>
              Cost a batch now
            </Button>
          )}
        </div>
      ) : (
        <div className="space-y-3">
          {filtered.map((batch) => {
            const marginNum = batch.profit_margin_pct ? Number(batch.profit_margin_pct) : null;
            const isProfitable = marginNum !== null ? marginNum > 0 : false;

            return (
              <div
                key={batch.id}
                className="bg-white rounded-xl border border-stone-200 p-4 sm:p-5 shadow-sm hover:border-forest-300 transition-all duration-200 flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4"
              >
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2 flex-wrap">
                    <h3 className="font-bold text-stone-900 text-base font-serif">
                      {batch.batch_name}
                    </h3>
                    {marginNum !== null && (
                      <span
                        className={`text-[11px] font-semibold px-2 py-0.5 rounded-full ${
                          marginNum >= 30
                            ? 'bg-emerald-100 text-emerald-800'
                            : marginNum >= 10
                            ? 'bg-lime-100 text-lime-900'
                            : marginNum > 0
                            ? 'bg-amber-100 text-amber-800'
                            : 'bg-rose-100 text-rose-800'
                        }`}
                      >
                        {formatPercent(marginNum)} Margin
                      </span>
                    )}
                  </div>

                  <div className="flex items-center gap-3 text-xs text-stone-500 flex-wrap">
                    <span className="flex items-center gap-1">
                      <Calendar className="w-3.5 h-3.5" />
                      {new Date(batch.created_at).toLocaleDateString()}
                    </span>
                    <span>•</span>
                    <span>
                      Yield: <strong className="text-stone-700">{batch.sellable_quantity} {batch.unit_name}</strong>
                    </span>
                    <span>•</span>
                    <span>
                      Cost / unit:{' '}
                      <strong className="text-stone-700">
                        {formatRupee(batch.cost_per_sellable_unit)}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Financial Overview */}
                <div className="flex items-center gap-6 w-full sm:w-auto justify-between sm:justify-end border-t sm:border-t-0 pt-3 sm:pt-0 border-stone-100">
                  <div className="text-left sm:text-right">
                    <span className="text-[11px] text-stone-500 block">Total Batch Cost</span>
                    <strong className="text-base text-stone-900 font-bold">
                      {formatRupee(batch.total_batch_cost)}
                    </strong>
                  </div>

                  {batch.projected_profit && (
                    <div className="text-right">
                      <span className="text-[11px] text-stone-500 block">Projected Profit</span>
                      <strong
                        className={`text-base font-bold ${
                          isProfitable ? 'text-emerald-700' : 'text-rose-700'
                        }`}
                      >
                        {formatRupee(batch.projected_profit)}
                      </strong>
                    </div>
                  )}

                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setSelectedBatchId(batch.id)}
                      className="p-2 text-stone-600 hover:text-forest-900 hover:bg-stone-100 rounded-lg transition-colors"
                      title="View Details"
                    >
                      <Eye className="w-4 h-4" />
                    </button>
                    <button
                      type="button"
                      onClick={() => setBatchToDelete(batch)}
                      className="p-2 text-stone-400 hover:text-rose-600 hover:bg-rose-50 rounded-lg transition-colors"
                      title="Delete Record"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Batch Detail Modal */}
      <BatchDetailModal
        isOpen={Boolean(selectedBatchId)}
        onClose={() => setSelectedBatchId(null)}
        batchId={selectedBatchId}
        onCloneToWorkspace={onCloneToWorkspace}
      />

      {/* Confirm Delete */}
      <ConfirmDialog
        isOpen={Boolean(batchToDelete)}
        title="Delete Batch Record"
        message={`Are you sure you want to delete the record for "${batchToDelete?.batch_name}"? This action cannot be undone.`}
        confirmLabel="Delete Record"
        variant="danger"
        isLoading={isDeleting}
        onConfirm={handleDelete}
        onCancel={() => setBatchToDelete(null)}
      />
    </div>
  );
};
