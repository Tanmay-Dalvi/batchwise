import React from 'react';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'forest' | 'lime' | 'amber' | 'rose' | 'neutral' | 'blue';
  size?: 'sm' | 'md';
  icon?: React.ReactNode;
}

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'forest',
  size = 'md',
  icon,
}) => {
  const sizeClasses = {
    sm: 'text-[11px] px-2 py-0.5 gap-1',
    md: 'text-xs px-2.5 py-1 gap-1.5',
  }[size];

  const variantClasses = {
    forest: 'bg-forest-100 text-forest-900 border border-forest-200 font-medium',
    lime: 'bg-lime-100 text-lime-900 border border-lime-300 font-semibold',
    amber: 'bg-amber-100 text-amber-900 border border-amber-200 font-medium',
    rose: 'bg-rose-100 text-rose-800 border border-rose-200 font-medium',
    neutral: 'bg-stone-100 text-stone-700 border border-stone-200 font-medium',
    blue: 'bg-blue-100 text-blue-900 border border-blue-200 font-medium',
  }[variant];

  return (
    <span className={`inline-flex items-center rounded-full ${sizeClasses} ${variantClasses}`}>
      {icon && <span className="inline-flex shrink-0">{icon}</span>}
      <span>{children}</span>
    </span>
  );
};

