import { describe, it, expect, vi } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { CostSummaryCard } from '../components/costing/CostSummaryCard';
import { BatchCalculationResult } from '../types/costing';

const canonicalBesanLadooResult: BatchCalculationResult = {
  batch_name: 'Besan Ladoo 75-pack batch',
  unit_name: 'packets',
  total_ingredients_cost: '780.00',
  packaging_cost: '80.00',
  labour_cost: '0.00',
  fuel_cost: '0.00',
  delivery_cost: '0.00',
  other_expenses: '0.00',
  direct_wastage_expense: '0.00',
  total_overheads: '80.00',
  total_batch_cost: '860.00',
  sellable_quantity: '75',
  cost_per_sellable_unit: '11.47',
  break_even_price_per_unit: '11.47',
  planned_selling_price: '25.00',
  projected_revenue: '1875.00',
  projected_profit: '1015.00',
  profit_per_unit: '13.53',
  profit_margin_pct: '54.13',
  markup_pct: '118.02',
  break_even_units_to_sell: '35',
  target_margin_pct: '40.00',
  target_margin_selling_price: '19.12',
  target_margin_profit_per_unit: '7.65',
  target_margin_markup_pct: '66.67',
  ingredient_results: [
    {
      name: 'Besan',
      recipe_quantity: '5',
      recipe_unit: 'kg',
      purchase_quantity: '5',
      purchase_unit: 'kg',
      purchase_price: '600.00',
      cost: '600.00',
      exact_cost: '600.0000',
      audit_step: {
        step_name: 'ingredient_cost_Besan',
        formula: 'purchase_price * (recipe_quantity / purchase_quantity)',
        inputs: {},
        result: '600.00',
        explanation: '5 kg @ 600',
      },
    },
    {
      name: 'Oil',
      recipe_quantity: '1',
      recipe_unit: 'L',
      purchase_quantity: '1',
      purchase_unit: 'L',
      purchase_price: '180.00',
      cost: '180.00',
      exact_cost: '180.0000',
      audit_step: {
        step_name: 'ingredient_cost_Oil',
        formula: 'purchase_price * (recipe_quantity / purchase_quantity)',
        inputs: {},
        result: '180.00',
        explanation: '1 L @ 180',
      },
    },
  ],
  audit_trail: [
    {
      step_name: 'total_batch_cost',
      formula: 'total_ingredients + total_overheads',
      inputs: {},
      result: '860.00',
      explanation: '780 + 80',
    },
  ],
};

describe('CostSummaryCard component', () => {
  it('renders batch name, total cost, cost per unit, and break-even price', () => {
    render(<CostSummaryCard result={canonicalBesanLadooResult} />);

    expect(screen.getByText('Besan Ladoo 75-pack batch')).toBeInTheDocument();
    expect(screen.getByText('₹860.00')).toBeInTheDocument();
    expect(screen.getAllByText('₹11.47').length).toBeGreaterThanOrEqual(1);
    expect(screen.getByText('75 packets')).toBeInTheDocument();
  });

  it('displays profitability, margin (54.13%), markup (118.02%), and break-even units (35)', () => {
    render(<CostSummaryCard result={canonicalBesanLadooResult} />);

    expect(screen.getByText('Projected Profitability')).toBeInTheDocument();
    expect(screen.getByText('₹1,875.00')).toBeInTheDocument();
    expect(screen.getByText('₹1,015.00')).toBeInTheDocument();
    expect(screen.getByText('54.13%')).toBeInTheDocument();
    expect(screen.getByText('(118.02% markup)')).toBeInTheDocument();
    expect(screen.getByText(/Break-even: 35 units/i)).toBeInTheDocument();
  });

  it('opens and closes formula explanation', () => {
    render(<CostSummaryCard result={canonicalBesanLadooResult} />);

    const helpBtn = screen.getByText(/Margin vs Markup explained/i);
    fireEvent.click(helpBtn);

    expect(screen.getByText(/Profit Margin \(%\):/i)).toBeInTheDocument();
    expect(screen.getByText(/Markup \(%\):/i)).toBeInTheDocument();
  });

  it('shows target margin recommendation if provided', () => {
    render(<CostSummaryCard result={canonicalBesanLadooResult} />);

    expect(screen.getByText(/Target Margin Recommendation/i)).toBeInTheDocument();
    expect(screen.getByText('₹19.12')).toBeInTheDocument();
  });

  it('calls onSaveBatch when save button is clicked', () => {
    const handleSave = vi.fn();
    render(<CostSummaryCard result={canonicalBesanLadooResult} onSaveBatch={handleSave} />);

    const saveBtn = screen.getByText('Save Batch');
    fireEvent.click(saveBtn);

    expect(handleSave).toHaveBeenCalledTimes(1);
  });
});
