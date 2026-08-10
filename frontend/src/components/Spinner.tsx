import { FC } from 'react';

export const Spinner: FC = () => {
  return (
    <div className="flex items-center justify-center" role="status" aria-label="Loading">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-indigo-500 border-t-transparent"></div>
    </div>
  );
};
