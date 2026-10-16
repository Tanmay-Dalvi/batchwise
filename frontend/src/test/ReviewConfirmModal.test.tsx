import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { ReviewConfirmModal } from '../components/ai/ReviewConfirmModal';
import { CandidateBatchExtraction } from '../types/ai';

const sampleCandidate: CandidateBatchExtraction = {
  raw_note: '5 kg besan cost 600 rupees, oil 180, packaging 80, made 75 packets, sold each for 25.',
  batch_name: 'Besan Ladoo Batch',
  ingredients: [
    {
      name: 'Besan',
      recipe_quantity: '5',
      recipe_unit: 'kg',
      purchase_quantity: '5',
      purchase_unit: 'kg',
      purchase_price: '600',
    },
    {
      name: 'Oil',
      recipe_quantity: '1',
      recipe_unit: 'L',
      purchase_price: '180',
    },
  ],
  packaging_cost: '80',
  labour_cost: '0',
  fuel_cost: '0',
  delivery_cost: '0',
  other_expenses: '0',
  sellable_quantity: '75',
  yield_unit_name: 'packets',
  planned_selling_price: '25',
  missing_fields: ['labour_cost', 'fuel_cost'],
  ambiguities: [
    {
      field_name: 'oil',
      raw_text: 'oil 180',
      question: 'Assumed 1 unit/pack for oil at ₹180. Verify unit.',
      options: ['1 L', '1 bottle', '1 packet'],
    },
  ],
  confidence_summary: 'High confidence for ingredients and yield.',
  can_calculate: true,
};

describe('ReviewConfirmModal component', () => {
  it('does not render when isOpen is false', () => {
    render(
      <ReviewConfirmModal
        isOpen={false}
        onClose={vi.fn()}
        candidate={sampleCandidate}
        onApply={vi.fn()}
      />
    );

    expect(screen.queryByText(/Review AI Extracted Batch/i)).not.toBeInTheDocument();
  });

  it('renders raw note, extracted ingredients, and ambiguity alerts when open', () => {
    render(
      <ReviewConfirmModal
        isOpen={true}
        onClose={vi.fn()}
        candidate={sampleCandidate}
        onApply={vi.fn()}
      />
    );

    expect(screen.getByText(/Review AI Extracted Batch/i)).toBeInTheDocument();
    expect(screen.getByText(new RegExp(sampleCandidate.raw_note, 'i'))).toBeInTheDocument();
    expect(screen.getByDisplayValue('Besan')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Oil')).toBeInTheDocument();
    expect(screen.getByText(/Ambiguous items require verification:/i)).toBeInTheDocument();
    expect(screen.getByText(/oil:/i)).toBeInTheDocument();
  });

  it('calls onApply with updated inputs when Apply to Workspace is clicked', () => {
    const handleApply = vi.fn();
    const handleClose = vi.fn();

    render(
      <ReviewConfirmModal
        isOpen={true}
        onClose={handleClose}
        candidate={sampleCandidate}
        onApply={handleApply}
      />
    );

    const applyBtn = screen.getByText(/Apply to Workspace/i);
    fireEvent.click(applyBtn);

    expect(handleApply).toHaveBeenCalledTimes(1);
    const appliedInput = handleApply.mock.calls[0][0];
    expect(appliedInput.batch_name).toBe('Besan Ladoo Batch');
    expect(appliedInput.ingredients.length).toBe(2);
    expect(appliedInput.packaging_cost).toBe('80');
    expect(appliedInput.batch_yield.sellable_quantity).toBe('75');
    expect(handleClose).toHaveBeenCalledTimes(1);
  });
});
