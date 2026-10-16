import React from 'react';
import { ShieldCheck, Cpu } from 'lucide-react';

export const Footer: React.FC = () => {
  return (
    <footer className="mt-16 border-t border-stone-200 bg-white/70 py-10 text-stone-600 text-xs">
      <div className="max-w-6xl mx-auto px-4 sm:px-6">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 pb-8 border-b border-stone-200">
          <div>
            <div className="flex items-center gap-2 text-charcoal-900 font-bold text-sm mb-2">
              <span className="w-2 h-2 rounded-full bg-forest-700"></span>
              Why the name Batchwise?
            </div>
            <p className="text-stone-600 leading-relaxed text-xs">
              <strong className="text-charcoal-900">Batch</strong> refers to a real production batch—one preparation of snacks, baked goods, or meals consuming ingredients, labour, and fuel. <strong className="text-charcoal-900">Wise</strong> represents informed, data-driven financial decisions. Batchwise means making smarter business decisions, one production batch at a time.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 text-charcoal-900 font-bold text-sm mb-2">
              <ShieldCheck className="w-4 h-4 text-forest-700" />
              Local-First Privacy Guarantee
            </div>
            <p className="text-stone-600 leading-relaxed text-xs">
              Your secret family recipes, supplier pricing, and profit margins stay strictly on your device. The deterministic calculation engine and local Gemma 3 1B model run entirely on your machine.
            </p>
          </div>

          <div>
            <div className="flex items-center gap-2 text-charcoal-900 font-bold text-sm mb-2">
              <Cpu className="w-4 h-4 text-forest-700" />
              Built for Hacktoberfest 2026
            </div>
            <p className="text-stone-600 leading-relaxed text-xs">
              Week 2 “Side Hustle” Challenge: Building open-weight AI products that small business owners would actually pay for. Powered by Python Decimal arithmetic and Gemma 3 1B on Ollama.
            </p>
          </div>
        </div>

        <div className="pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-[11px] text-stone-500">
          <div>
            &copy; 2026 Batchwise Open Source Project. Licensed under the MIT License.
          </div>
          <div className="flex items-center gap-4">
            <span className="font-mono">“Every batch. Every cost. Every rupee.”</span>
          </div>
        </div>
      </div>
    </footer>
  );
};

