import React, { useState, useEffect } from 'react';
import { RecipeResponse } from '../../types/recipe';
import { api } from '../../lib/api';
import { formatRupee } from '../../lib/currency';
import { Button } from '../common/Button';
import { ConfirmDialog } from '../common/ConfirmDialog';
import { RecipeModal } from './RecipeModal';
import {
  Plus,
  BookOpen,
  Search,
  Calculator,
  Edit2,
  Trash2,
  Package,
  Layers,
} from 'lucide-react';

interface RecipeListViewProps {
  onCostRecipe: (recipe: RecipeResponse) => void;
}

export const RecipeListView: React.FC<RecipeListViewProps> = ({ onCostRecipe }) => {
  const [recipes, setRecipes] = useState<RecipeResponse[]>([]);
  const [search, setSearch] = useState('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingRecipe, setEditingRecipe] = useState<RecipeResponse | null>(null);

  // Delete Dialog State
  const [recipeToDelete, setRecipeToDelete] = useState<RecipeResponse | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  const fetchRecipes = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const data = await api.listRecipes();
      setRecipes(data);
    } catch (err: any) {
      setError('Unable to load recipes. Please check your connection.');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchRecipes();
  }, []);

  const handleCreate = () => {
    setEditingRecipe(null);
    setIsModalOpen(true);
  };

  const handleEdit = (recipe: RecipeResponse) => {
    setEditingRecipe(recipe);
    setIsModalOpen(true);
  };

  const handleSaved = (_saved: RecipeResponse) => {
    fetchRecipes();
  };

  const handleDeleteConfirm = async () => {
    if (!recipeToDelete) return;
    setIsDeleting(true);
    try {
      await api.deleteRecipe(recipeToDelete.id);
      setRecipes((prev) => prev.filter((r) => r.id !== recipeToDelete.id));
      setRecipeToDelete(null);
    } catch (err) {
      console.error('Failed to delete recipe', err);
    } finally {
      setIsDeleting(false);
    }
  };

  const filtered = recipes.filter((r) =>
    r.name.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="max-w-4xl mx-auto space-y-6 pb-12">
      {/* Header */}
      <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <span className="text-xs font-semibold uppercase tracking-wider text-forest-700">
            Standard Master Formulas
          </span>
          <h2 className="text-xl sm:text-2xl font-bold font-serif text-stone-900">
            Recipe Templates
          </h2>
          <p className="text-xs sm:text-sm text-stone-500">
            Save reusable ingredient lists and standard overheads to cost batches in seconds.
          </p>
        </div>

        <Button
          variant="primary"
          size="sm"
          onClick={handleCreate}
          className="bg-forest-900 hover:bg-forest-950 text-white font-medium"
        >
          <Plus className="w-4 h-4 mr-1.5 text-lime-400" />
          <span>New Recipe</span>
        </Button>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="w-4 h-4 text-stone-400 absolute left-3 top-1/2 -translate-y-1/2" />
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search recipes by name..."
          className="w-full pl-9 pr-4 py-2 text-xs sm:text-sm bg-white rounded-xl border border-stone-200 focus:outline-none focus:ring-2 focus:ring-forest-600"
        />
      </div>

      {/* Recipe List */}
      {isLoading ? (
        <div className="text-center py-12 text-stone-500 text-sm">
          Loading recipes...
        </div>
      ) : error ? (
        <div className="p-4 bg-rose-50 border border-rose-200 rounded-xl text-rose-800 text-sm text-center">
          {error}
        </div>
      ) : filtered.length === 0 ? (
        <div className="bg-white rounded-xl border border-dashed border-stone-300 p-10 text-center space-y-3">
          <BookOpen className="w-10 h-10 text-stone-400 mx-auto" />
          <h3 className="font-semibold text-stone-800 text-base">No recipes found</h3>
          <p className="text-xs sm:text-sm text-stone-500 max-w-sm mx-auto">
            {search
              ? 'No recipes match your search query.'
              : 'Create reusable recipes for your snacks, cakes, or meals to speed up batch costing.'}
          </p>
          {!search && (
            <Button variant="outline" size="sm" onClick={handleCreate}>
              <Plus className="w-4 h-4 mr-1 text-forest-700" />
              Create your first recipe
            </Button>
          )}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filtered.map((recipe) => (
            <div
              key={recipe.id}
              className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm hover:border-forest-300 transition-all duration-200 flex flex-col justify-between"
            >
              <div>
                <div className="flex justify-between items-start gap-2">
                  <h3 className="font-semibold text-stone-900 text-base font-serif">
                    {recipe.name}
                  </h3>
                  <span className="text-[11px] font-medium bg-forest-50 text-forest-800 px-2 py-0.5 rounded-full border border-forest-100">
                    {recipe.yield_unit}
                  </span>
                </div>
                {recipe.description && (
                  <p className="text-xs text-stone-500 mt-1 line-clamp-2">
                    {recipe.description}
                  </p>
                )}

                <div className="mt-4 pt-3 border-t border-stone-100 grid grid-cols-2 gap-2 text-xs text-stone-600">
                  <div className="flex items-center gap-1.5">
                    <Layers className="w-3.5 h-3.5 text-stone-400" />
                    <span>{recipe.ingredients.length} ingredients</span>
                  </div>
                  <div className="flex items-center gap-1.5">
                    <Package className="w-3.5 h-3.5 text-stone-400" />
                    <span>
                      Packaging:{' '}
                      <strong className="text-stone-800">
                        {formatRupee(recipe.default_packaging_cost)}
                      </strong>
                    </span>
                  </div>
                </div>

                {/* Ingredients Pills */}
                <div className="mt-3 flex flex-wrap gap-1">
                  {recipe.ingredients.slice(0, 4).map((ing, i) => (
                    <span
                      key={i}
                      className="text-[11px] bg-stone-100 text-stone-700 px-2 py-0.5 rounded"
                    >
                      {ing.name} ({ing.recipe_quantity} {ing.recipe_unit})
                    </span>
                  ))}
                  {recipe.ingredients.length > 4 && (
                    <span className="text-[11px] bg-stone-100 text-stone-500 px-1.5 py-0.5 rounded">
                      +{recipe.ingredients.length - 4} more
                    </span>
                  )}
                </div>
              </div>

              {/* Actions Footer */}
              <div className="mt-5 pt-3 border-t border-stone-100 flex items-center justify-between gap-2">
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() => onCostRecipe(recipe)}
                  className="bg-forest-900 hover:bg-forest-950 text-white text-xs"
                >
                  <Calculator className="w-3.5 h-3.5 mr-1 text-lime-400" />
                  <span>Cost Batch</span>
                </Button>

                <div className="flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => handleEdit(recipe)}
                    className="p-1.5 text-stone-500 hover:text-stone-800 rounded transition-colors"
                    title="Edit recipe"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    type="button"
                    onClick={() => setRecipeToDelete(recipe)}
                    className="p-1.5 text-stone-400 hover:text-rose-600 rounded transition-colors"
                    title="Delete recipe"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Recipe Modal */}
      <RecipeModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        recipe={editingRecipe}
        onSaved={handleSaved}
      />

      {/* Delete Confirmation */}
      <ConfirmDialog
        isOpen={Boolean(recipeToDelete)}
        title="Delete Recipe"
        message={`Are you sure you want to delete "${recipeToDelete?.name}"? Saved batch records based on this recipe will not be affected.`}
        confirmLabel="Delete Recipe"
        variant="danger"
        isLoading={isDeleting}
        onConfirm={handleDeleteConfirm}
        onCancel={() => setRecipeToDelete(null)}
      />
    </div>
  );
};
