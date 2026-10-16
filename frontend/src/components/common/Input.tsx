import React from 'react';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  helperText?: string;
  prefixText?: string;
  suffixText?: string;
}

export const Input: React.FC<InputProps> = ({
  label,
  error,
  helperText,
  prefixText,
  suffixText,
  id,
  className = '',
  required,
  ...props
}) => {
  const inputId = id || (label ? label.toLowerCase().replace(/\s+/g, '-') : undefined);

  return (
    <div className="w-full">
      {label && (
        <label htmlFor={inputId} className="block text-xs font-semibold text-charcoal-800 uppercase tracking-wider mb-1">
          {label} {required && <span className="text-rose-500">*</span>}
        </label>
      )}
      <div className="relative rounded-lg shadow-xs flex items-center">
        {prefixText && (
          <span className="inline-flex items-center px-3 rounded-l-lg border border-r-0 border-stone-300 bg-cream-200 text-stone-600 text-sm font-medium select-none">
            {prefixText}
          </span>
        )}
        <input
          id={inputId}
          className={`block w-full text-sm rounded-lg border bg-white px-3 py-2 text-charcoal-900 placeholder-stone-400 focus:outline-none focus:ring-2 transition-colors ${
            prefixText ? 'rounded-l-none' : ''
          } ${suffixText ? 'rounded-r-none' : ''} ${
            error
              ? 'border-rose-400 focus:border-rose-500 focus:ring-rose-200'
              : 'border-stone-300 focus:border-forest-600 focus:ring-forest-100'
          } ${className}`}
          required={required}
          {...props}
        />
        {suffixText && (
          <span className="inline-flex items-center px-3 rounded-r-lg border border-l-0 border-stone-300 bg-cream-200 text-stone-600 text-xs font-medium select-none">
            {suffixText}
          </span>
        )}
      </div>
      {error && <p className="mt-1 text-xs text-rose-600 font-medium">{error}</p>}
      {helperText && !error && <p className="mt-1 text-xs text-stone-500">{helperText}</p>}
    </div>
  );
};

