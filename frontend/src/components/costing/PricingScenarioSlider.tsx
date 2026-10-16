import React from 'react';
import { Sliders, ArrowRight } from 'lucide-react';

interface PricingScenarioSliderProps {
  currentSellingPrice: string;
  currentTargetMargin: string;
  onPriceChange: (price: string) => void;
  onMarginChange: (margin: string) => void;
  onApplyScenario: () => void;
  isCalculating?: boolean;
}

export const PricingScenarioSlider: React.FC<PricingScenarioSliderProps> = ({
  currentSellingPrice,
  currentTargetMargin,
  onPriceChange,
  onMarginChange,
  onApplyScenario,
  isCalculating = false,
}) => {
  const marginPresets = ['20', '30', '40', '50', '60'];

  return (
    <div className="bg-stone-50 rounded-xl border border-stone-200 p-4 sm:p-5 mt-4">
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Sliders className="w-4 h-4 text-forest-700" />
          <h4 className="text-sm font-semibold text-stone-900">
            Pricing & Margin Scenario Simulator
          </h4>
        </div>
        <span className="text-xs text-stone-500">
          Simulate target margins or test different price points
        </span>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {/* Margin Target Presets */}
        <div>
          <label className="text-xs font-medium text-stone-700 block mb-1.5">
            Target Profit Margin (%)
          </label>
          <div className="flex items-center gap-1.5 flex-wrap">
            {marginPresets.map((pct) => {
              const isSelected = currentTargetMargin === pct;
              return (
                <button
                  key={pct}
                  type="button"
                  onClick={() => onMarginChange(pct)}
                  className={`px-2.5 py-1 text-xs rounded-md font-medium transition-colors ${
                    isSelected
                      ? 'bg-forest-800 text-white'
                      : 'bg-white border border-stone-200 text-stone-700 hover:bg-stone-100'
                  }`}
                >
                  {pct}%
                </button>
              );
            })}
            <div className="relative w-24">
              <input
                type="number"
                placeholder="Custom %"
                min="1"
                max="99"
                step="0.5"
                value={currentTargetMargin}
                onChange={(e) => onMarginChange(e.target.value)}
                className="w-full text-xs px-2 py-1 rounded-md border border-stone-200 bg-white focus:outline-none focus:ring-1 focus:ring-forest-600"
              />
            </div>
          </div>
        </div>

        {/* Planned Selling Price Quick Input */}
        <div>
          <label className="text-xs font-medium text-stone-700 block mb-1.5">
            Selling Price (₹ per unit)
          </label>
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <span className="absolute left-2.5 top-1/2 -translate-y-1/2 text-stone-400 text-xs font-medium">
                ₹
              </span>
              <input
                type="number"
                placeholder="0.00"
                min="0"
                step="0.5"
                value={currentSellingPrice}
                onChange={(e) => onPriceChange(e.target.value)}
                className="w-full pl-6 pr-2 py-1 text-xs sm:text-sm rounded-md border border-stone-200 bg-white focus:outline-none focus:ring-1 focus:ring-forest-600"
              />
            </div>
            <button
              type="button"
              onClick={onApplyScenario}
              disabled={isCalculating}
              className="px-3 py-1.5 bg-forest-800 hover:bg-forest-900 text-white text-xs font-medium rounded-md flex items-center gap-1 transition-colors disabled:opacity-50"
            >
              <span>{isCalculating ? 'Computing...' : 'Recalculate'}</span>
              <ArrowRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

