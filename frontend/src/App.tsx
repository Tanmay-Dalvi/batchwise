import React, { useState, useEffect } from 'react';
import { Header, ActiveTab } from './components/layout/Header';
import { Footer } from './components/layout/Footer';
import { DashboardView } from './components/dashboard/DashboardView';
import { CostingWorkspace } from './components/costing/CostingWorkspace';
import { NoteInputBar } from './components/ai/NoteInputBar';
import { ReviewConfirmModal } from './components/ai/ReviewConfirmModal';
import { RecipeListView } from './components/recipes/RecipeListView';
import { BatchHistoryView } from './components/batches/BatchHistoryView';
import { api } from './lib/api';
import { BatchCostingInput, BatchRecordDetailResponse } from './types/costing';
import { RecipeResponse } from './types/recipe';
import { CandidateBatchExtraction, ParseNoteResponse } from './types/ai';

export const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('dashboard');
  const [isBackendHealthy, setIsBackendHealthy] = useState<boolean | null>(null);

  // Cross-view state transfer for CostingWorkspace
  const [workspaceInitialData, setWorkspaceInitialData] = useState<
    Partial<BatchCostingInput> | undefined
  >(undefined);

  // AI Review Staging state
  const [candidateExtraction, setCandidateExtraction] =
    useState<CandidateBatchExtraction | null>(null);
  const [isReviewModalOpen, setIsReviewModalOpen] = useState(false);
  const [isExtractingAi, setIsExtractingAi] = useState(false);

  // Initial and periodic health check
  useEffect(() => {
    async function checkHealth() {
      try {
        const res = await api.getHealth();
        setIsBackendHealthy(res.status === 'ok');
      } catch (err) {
        setIsBackendHealthy(false);
      }
    }

    checkHealth();
    const interval = setInterval(checkHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Handler: When user wants to cost a saved recipe
  const handleCostRecipe = (recipe: RecipeResponse) => {
    setWorkspaceInitialData({
      batch_name: `${recipe.name} Batch`,
      packaging_cost: recipe.default_packaging_cost || '0',
      labour_cost: recipe.default_labour_cost || '0',
      fuel_cost: recipe.default_fuel_cost || '0',
      delivery_cost: recipe.default_delivery_cost || '0',
      other_expenses: recipe.default_other_expenses || '0',
      direct_wastage_expense: '0',
      batch_yield: {
        unit_name: recipe.yield_unit || 'packets',
        sellable_quantity: '50',
      },
      ingredients: recipe.ingredients.map((ing) => ({
        name: ing.name,
        recipe_quantity: ing.recipe_quantity,
        recipe_unit: ing.recipe_unit,
        purchase_quantity: ing.purchase_quantity || ing.recipe_quantity,
        purchase_unit: ing.purchase_unit || ing.recipe_unit,
        purchase_price: ing.purchase_price,
      })),
      planned_selling_price: '',
      target_margin_pct: '40',
    });
    setActiveTab('costing');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handler: When AI extracts a candidate batch note
  const handleAiExtractionSuccess = (response: ParseNoteResponse) => {
    if (response.candidate) {
      setCandidateExtraction(response.candidate);
      setIsReviewModalOpen(true);
    }
  };

  // Handler: When user reviews & applies candidate AI inputs
  const handleApplyAiExtraction = (costingInput: BatchCostingInput) => {
    setWorkspaceInitialData(costingInput);
    setActiveTab('costing');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  // Handler: When user clones a historical batch
  const handleCloneBatch = (detail: BatchRecordDetailResponse) => {
    setWorkspaceInitialData(detail.calculation_input);
    setActiveTab('costing');
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  return (
    <div className="min-h-screen flex flex-col bg-[#FAF8F5] text-stone-900 font-sans antialiased">
      {/* Top Application Header */}
      <Header
        activeTab={activeTab}
        onTabChange={(tab) => {
          setActiveTab(tab);
          window.scrollTo({ top: 0, behavior: 'smooth' });
        }}
        isBackendHealthy={isBackendHealthy}
      />

      {/* Main View Area */}
      <main className="flex-1 max-w-6xl w-full mx-auto px-4 sm:px-6 py-6 sm:py-8">
        {activeTab === 'dashboard' && (
          <DashboardView
            onNavigateToCosting={() => setActiveTab('costing')}
            onNavigateToAiNotes={() => setActiveTab('ai')}
            onNavigateToRecipes={() => setActiveTab('recipes')}
            onNavigateToHistory={() => setActiveTab('history')}
            onCostRecipe={handleCostRecipe}
          />
        )}

        {activeTab === 'costing' && (
          <CostingWorkspace
            initialData={workspaceInitialData}
            onOpenAiNotes={() => setActiveTab('ai')}
            onBatchSaved={() => {
              // Reset initial data if saved
            }}
          />
        )}

        {activeTab === 'ai' && (
          <div className="max-w-4xl mx-auto space-y-6">
            <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm">
              <span className="text-xs font-semibold uppercase tracking-wider text-forest-700">
                Natural Language Costing
              </span>
              <h2 className="text-xl sm:text-2xl font-bold font-serif text-stone-900 mt-0.5">
                Messy Notes to Batch Costing
              </h2>
              <p className="text-xs sm:text-sm text-stone-500 mt-1">
                Type or paste vendor purchase notes in Hindi-English or plain conversational English.
                Gemma 3 1B structures ingredients and prices; pure arithmetic determines profitability.
              </p>
            </div>

            <NoteInputBar
              onExtractionSuccess={handleAiExtractionSuccess}
              isExtracting={isExtractingAi}
              setIsExtracting={setIsExtractingAi}
            />
          </div>
        )}

        {activeTab === 'recipes' && (
          <RecipeListView onCostRecipe={handleCostRecipe} />
        )}

        {activeTab === 'history' && (
          <BatchHistoryView
            onCostNewBatch={() => setActiveTab('costing')}
            onCloneToWorkspace={handleCloneBatch}
          />
        )}
      </main>

      {/* AI Extraction Staging & Confirmation Drawer / Modal */}
      <ReviewConfirmModal
        isOpen={isReviewModalOpen}
        onClose={() => setIsReviewModalOpen(false)}
        candidate={candidateExtraction}
        onApply={handleApplyAiExtraction}
      />

      {/* Application Footer */}
      <Footer />
    </div>
  );
};

export default App;

