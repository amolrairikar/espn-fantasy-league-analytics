import { Button } from '@/components/ui/button';
import React from 'react';

interface LoadingButtonProps {
  onClick: () => void | Promise<void>;
  loading: boolean;
  children?: React.ReactNode;
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({ onClick, loading, children = 'Submit' }) => {
  return (
    <Button onClick={() => void onClick()} className="cursor-pointer flex items-center gap-2" disabled={loading}>
      {loading ? (
        <>
          <svg
            className="animate-spin h-4 w-4 text-white"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
          </svg>
        </>
      ) : (
        children
      )}
    </Button>
  );
};
