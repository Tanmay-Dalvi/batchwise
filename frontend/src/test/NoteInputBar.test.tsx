import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { NoteInputBar } from '../components/ai/NoteInputBar';
import { api } from '../lib/api';

vi.mock('../lib/api', () => ({
  api: {
    getAiStatus: vi.fn(),
    parseNote: vi.fn(),
  },
  ApiError: class ApiError extends Error {
    status: number;
    constructor(message: string, status = 400) {
      super(message);
      this.status = status;
    }
  },
}));

describe('NoteInputBar component', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders Google Gemini provider badge and title when active provider is gemini', async () => {
    vi.mocked(api.getAiStatus).mockResolvedValueOnce({
      provider: 'gemini',
      model: 'gemini-1.5-flash',
      is_configured: true,
      description: 'Google Gemini (gemini-1.5-flash) Hosted Cloud AI',
    });

    render(
      <NoteInputBar
        onExtractionSuccess={vi.fn()}
        isExtracting={false}
        setIsExtracting={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/AI Note Parser \(Google Gemini\)/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Cloud AI: gemini-1.5-flash/i)).toBeInTheDocument();
    expect(screen.getByText(/Powered by Google Gemini API/i)).toBeInTheDocument();
  });

  it('renders local Ollama badge and title when active provider is ollama', async () => {
    vi.mocked(api.getAiStatus).mockResolvedValueOnce({
      provider: 'ollama',
      model: 'gemma3:1b',
      is_configured: true,
      description: 'Gemma 3 (gemma3:1b) on Local Ollama (Private)',
    });

    render(
      <NoteInputBar
        onExtractionSuccess={vi.fn()}
        isExtracting={false}
        setIsExtracting={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/AI Note Parser \(Gemma 3 1B\)/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Local & Private \(Ollama\)/i)).toBeInTheDocument();
    expect(screen.getByText(/Powered by local Gemma 3 1B on Ollama/i)).toBeInTheDocument();
  });

  it('populates textarea when clicking a sample chip', async () => {
    vi.mocked(api.getAiStatus).mockResolvedValueOnce({
      provider: 'gemini',
      model: 'gemini-1.5-flash',
      is_configured: true,
      description: 'Google Gemini',
    });

    render(
      <NoteInputBar
        onExtractionSuccess={vi.fn()}
        isExtracting={false}
        setIsExtracting={vi.fn()}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/AI Note Parser \(Google Gemini\)/i)).toBeInTheDocument();
    });

    const sampleChip = screen.getByText('Besan Ladoo (Canonical)');
    fireEvent.click(sampleChip);

    const textarea = screen.getByRole('textbox') as HTMLTextAreaElement;
    expect(textarea.value).toContain('5 kg besan cost 600 rupees');
  });

  it('calls parseNote on extract button click and triggers onExtractionSuccess', async () => {
    vi.mocked(api.getAiStatus).mockResolvedValueOnce({
      provider: 'gemini',
      model: 'gemini-1.5-flash',
      is_configured: true,
      description: 'Google Gemini',
    });

    vi.mocked(api.parseNote).mockResolvedValueOnce({
      success: true,
      status: 'success',
      provider_used: 'gemini',
      model_used: 'gemini-1.5-flash',
      candidate: {
        raw_note: '5 kg besan 600',
        batch_name: 'Besan Batch',
        ingredients: [],
        missing_fields: [],
        ambiguities: [],
        confidence_summary: 'Ready',
        can_calculate: true,
      },
    });

    const onExtractionSuccess = vi.fn();
    const setIsExtracting = vi.fn();

    render(
      <NoteInputBar
        onExtractionSuccess={onExtractionSuccess}
        isExtracting={false}
        setIsExtracting={setIsExtracting}
      />
    );

    await waitFor(() => {
      expect(screen.getByText(/AI Note Parser \(Google Gemini\)/i)).toBeInTheDocument();
    });

    const sampleChip = screen.getByText('Besan Ladoo (Canonical)');
    fireEvent.click(sampleChip);

    const extractBtn = screen.getByRole('button', { name: /Extract Structured Batch/i });
    fireEvent.click(extractBtn);

    await waitFor(() => {
      expect(api.parseNote).toHaveBeenCalledWith(expect.stringContaining('5 kg besan'));
      expect(onExtractionSuccess).toHaveBeenCalled();
    });
  });
});
