import React, { useEffect, useState } from 'react';
import { api, ApiError } from '../../lib/api';
import { AiStatusResponse, ParseNoteResponse } from '../../types/ai';
import { Button } from '../common/Button';
import {
  Sparkles,
  Bot,
  AlertCircle,
  FileText,
  CornerDownLeft,
  Cloud,
  ShieldCheck,
} from 'lucide-react';

interface NoteInputBarProps {
  onExtractionSuccess: (response: ParseNoteResponse) => void;
  isExtracting: boolean;
  setIsExtracting: (val: boolean) => void;
}

const SAMPLE_NOTES = [
  {
    title: 'Besan Ladoo (Canonical)',
    text: '5 kg besan cost 600 rupees, oil 180, packaging 80, made 75 packets, sold each for 25.',
  },
  {
    title: 'Home Baker Sourdough',
    text: 'Sourdough batch: 2 kg flour 140, yeast 30, butter 120, electricity 50, baked 8 loaves, selling for 90 each.',
  },
  {
    title: 'Tiffin Service Lunch',
    text: 'Daily lunch tiffin: 3 kg rice 180, 1 kg urad dal 160, oil 90, gas 60, packed 40 tiffins at 60 rupees each.',
  },
  {
    title: 'Tea Stall Samosas',
    text: 'Evening batch: 4 kg potatoes 120, 2 kg flour 80, oil 200, spices 50, made 100 samosas, sold for 12 each.',
  },
];

export const NoteInputBar: React.FC<NoteInputBarProps> = ({
  onExtractionSuccess,
  isExtracting,
  setIsExtracting,
}) => {
  const [note, setNote] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [aiStatus, setAiStatus] = useState<AiStatusResponse | null>(null);

  useEffect(() => {
    let isMounted = true;
    api.getAiStatus()
      .then((status) => {
        if (isMounted) {
          setAiStatus(status);
        }
      })
      .catch(() => {
        // Silently keep default fallback
      });
    return () => {
      isMounted = false;
    };
  }, []);

  const isGemini = aiStatus?.provider === 'gemini';
  const modelName = aiStatus?.model || (isGemini ? 'gemini-2.5-flash' : 'gemma3:1b');

  const handleExtract = async () => {
    if (!note.trim()) {
      setError('Please type or select a note first.');
      return;
    }

    setError(null);
    setIsExtracting(true);

    try {
      const response = await api.parseNote(note);
      if (response.success && response.candidate) {
        onExtractionSuccess(response);
      } else {
        setError(
          response.error_message ||
            'AI parser could not structure the note. Please check your AI configuration or refine your text.'
        );
      }
    } catch (err: any) {
      if (err instanceof ApiError) {
        setError(err.message);
      } else {
        setError(
          isGemini
            ? 'Failed to reach AI parser service. Please check your backend connection or enter costs manually.'
            : 'Failed to reach local Ollama AI parser. Ensure Ollama is running or enter costs manually.'
        );
      }
    } finally {
      setIsExtracting(false);
    }
  };

  return (
    <div className="bg-white rounded-xl border border-stone-200 p-5 shadow-sm space-y-4">
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2">
        <div className="flex items-center gap-2">
          <div className="p-2 bg-forest-50 text-forest-800 rounded-lg">
            <Bot className="w-5 h-5 text-forest-700" />
          </div>
          <div>
            <h3 className="text-base font-semibold text-stone-900">
              {isGemini ? 'AI Note Parser (Google Gemini)' : 'AI Note Parser (Gemma 3 1B)'}
            </h3>
            <p className="text-xs text-stone-500">
              {isGemini
                ? 'Paste messy purchase notes. Cloud AI extracts candidate fields; pure Python Decimal calculates financial costs.'
                : 'Speak or paste raw purchase notes. Local AI structures it; the math engine does the rest.'}
            </p>
          </div>
        </div>

        {isGemini ? (
          <div className="text-[11px] font-medium bg-emerald-50 text-emerald-900 border border-emerald-200 px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-xs">
            <Cloud className="w-3.5 h-3.5 text-emerald-600" />
            <span>Cloud AI: {modelName}</span>
          </div>
        ) : (
          <div className="text-[11px] font-medium bg-lime-100 text-forest-900 px-2.5 py-1 rounded-full flex items-center gap-1.5 shadow-xs">
            <ShieldCheck className="w-3.5 h-3.5 text-forest-700" />
            <span>Local & Private (Ollama)</span>
          </div>
        )}
      </div>

      {/* Sample Note Chips */}
      <div>
        <span className="text-[11px] font-medium text-stone-500 block mb-1.5">
          Try a sample note:
        </span>
        <div className="flex flex-wrap gap-1.5">
          {SAMPLE_NOTES.map((sample, idx) => (
            <button
              key={idx}
              type="button"
              onClick={() => setNote(sample.text)}
              className="text-xs px-2.5 py-1 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-md transition-colors text-left flex items-center gap-1"
            >
              <FileText className="w-3 h-3 text-stone-400" />
              <span>{sample.title}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Note Textarea */}
      <div className="relative">
        <textarea
          rows={3}
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="e.g. 5 kg besan cost 600 rupees, oil 180, packaging 80, made 75 packets, sold each for 25."
          className="w-full text-xs sm:text-sm p-3 rounded-lg border border-stone-200 focus:outline-none focus:ring-2 focus:ring-forest-600 focus:border-forest-600 bg-stone-50/50 resize-y"
        />
      </div>

      {error && (
        <div className="p-3 bg-rose-50 border border-rose-200 rounded-lg flex items-center gap-2 text-rose-800 text-xs">
          <AlertCircle className="w-4 h-4 shrink-0 text-rose-600" />
          <span>{error}</span>
        </div>
      )}

      {/* Action footer */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3 pt-1">
        <span className="text-[11px] text-stone-500">
          {isGemini
            ? 'Powered by Google Gemini API (hosted cloud AI). Notes are sent to Gemini for staging extraction only. Financial arithmetic is strictly calculated by Batchwise. Manual batch costing is 100% available without AI.'
            : 'Powered by local Gemma 3 1B on Ollama. Private on-device extraction. On hosted cloud demos without local Ollama access, manual batch costing remains 100% functional.'}
        </span>

        <Button
          variant="primary"
          size="sm"
          onClick={handleExtract}
          disabled={isExtracting || !note.trim()}
          className="w-full sm:w-auto bg-forest-900 hover:bg-forest-950 text-white font-medium"
        >
          {isExtracting ? (
            isGemini ? 'Parsing with Gemini...' : 'Parsing with Gemma 3...'
          ) : (
            <>
              <Sparkles className="w-4 h-4 mr-1.5 text-lime-400" />
              <span>Extract Structured Batch</span>
              <CornerDownLeft className="w-3.5 h-3.5 ml-1.5 opacity-70" />
            </>
          )}
        </Button>
      </div>
    </div>
  );
};

