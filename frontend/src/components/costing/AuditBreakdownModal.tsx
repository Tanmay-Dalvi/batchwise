import React from 'react';
import { X, Calculator, ShieldCheck, CheckCircle2 } from 'lucide-react';
import { AuditStep } from '../../types/costing';
import { Button } from '../common/Button';

interface AuditBreakdownModalProps {
  isOpen: boolean;
  onClose: () => void;
  auditTrail: AuditStep[];
  batchName: string;
}

export const AuditBreakdownModal: React.FC<AuditBreakdownModalProps> = ({
  isOpen,
  onClose,
  auditTrail,
  batchName,
}) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-charcoal-950/50 backdrop-blur-xs animate-in fade-in duration-150">
      <div className="bg-white rounded-2xl shadow-2xl max-w-2xl w-full max-h-[85vh] flex flex-col border border-stone-200 overflow-hidden">
        {/* Header */}
        <div className="px-6 py-4 border-b border-stone-200 flex items-center justify-between bg-cream-50">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-forest-100 text-forest-900">
              <Calculator className="w-5 h-5" />
            </div>
            <div>
              <h3 className="text-base font-bold text-charcoal-900">
                Transparent Calculation Audit
              </h3>
              <p className="text-xs text-stone-500 font-medium">
                {batchName} &bull; Step-by-step verification
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg text-stone-400 hover:text-charcoal-900 hover:bg-stone-100 transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Audit Steps Body */}
        <div className="p-6 overflow-y-auto space-y-4">
          <div className="p-3 rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-900 text-xs flex items-start gap-2.5">
            <ShieldCheck className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
            <div>
              <span className="font-semibold">Deterministic Zero-Float Math Guarantee:</span> All financial values below were computed strictly using Python Decimal arithmetic and standard banking half-up rounding. Zero language-model hallucinations.
            </div>
          </div>

          <div className="space-y-3">
            {auditTrail.map((step, idx) => (
              <div
                key={idx}
                className="p-4 rounded-xl border border-stone-200 bg-cream-50/50 space-y-2 hover:border-stone-300 transition-colors"
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <CheckCircle2 className="w-4 h-4 text-forest-600 shrink-0" />
                    <span className="text-xs font-mono font-bold text-forest-900 uppercase tracking-wider">
                      {step.step_name}
                    </span>
                  </div>
                  <span className="font-mono text-xs font-bold px-2 py-0.5 rounded bg-white border border-stone-200 text-charcoal-900">
                    Result: {step.result}
                  </span>
                </div>

                <div className="bg-white p-2.5 rounded-lg border border-stone-200 font-mono text-[11px] text-stone-700 overflow-x-auto">
                  <span className="text-stone-400 select-none">Formula: </span>
                  {step.formula}
                </div>

                <p className="text-xs text-stone-600 leading-relaxed">
                  {step.explanation}
                </p>
              </div>
            ))}
          </div>
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-stone-200 bg-cream-50 flex items-center justify-end">
          <Button variant="primary" size="sm" onClick={onClose}>
            Close Audit
          </Button>
        </div>
      </div>
    </div>
  );
};

