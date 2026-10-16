import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { CostingWorkspace } from '../components/costing/CostingWorkspace';
import { api } from '../lib/api';

vi.mock('../lib/api', () => ({
  api: {
    listRecipes: vi.fn().mockResolvedValue([]),
    calculateBatch: vi.fn(),
    createBatch: vi.fn(),
    createRecipe: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status = 400) {
      super(message);
      this.status = status;
    }
  },
}));

describe('CostingWorkspace component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders initial ingredient rows and allows adding a row', async () => {
    render(<CostingWorkspace />);

    await waitFor(() => {
      expect(screen.getByText('Batch Costing Engine')).toBeInTheDocument();
    });
    expect(screen.getByDisplayValue('Besan (Gram Flour)')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Refined Oil / Ghee')).toBeInTheDocument();

    const addBtn = screen.getByText('Add Row');
    fireEvent.click(addBtn);

    const inputs = screen.getAllByPlaceholderText(/e\.g\. Besan, Ghee, Sugar/i);
    expect(inputs.length).toBe(3);
  });

  it('triggers calculation on calculate button click and shows results', async () => {
    vi.mocked(api.calculateBatch).mockResolvedValueOnce({
      batch_name: 'Besan Ladoo Batch',
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
      ingredient_results: [],
      audit_trail: [],
    });

    render(<CostingWorkspace />);

    const calculateBtn = screen.getByText(/Calculate Batch Cost & Profit/i);
    fireEvent.click(calculateBtn);

    await waitFor(() => {
      expect(api.calculateBatch).toHaveBeenCalledTimes(1);
    });

    expect(await screen.findByText('Calculation Results')).toBeInTheDocument();
    expect(screen.getByText('₹860.00')).toBeInTheDocument();
    expect(screen.getByText('54.13%')).toBeInTheDocument();
  });
});
