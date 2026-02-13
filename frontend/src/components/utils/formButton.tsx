import { Button } from '@/components/ui/button';
import React from 'react';

interface LoadingButtonProps {
  // Make onClick optional since type="submit" doesn't always need one
  onClick?: () => void | Promise<void>;
  loading: boolean;
  children?: React.ReactNode;
  // Add standard button types (submit, button, or reset)
  type?: 'submit' | 'button' | 'reset';
  className?: string;
}

export const LoadingButton: React.FC<LoadingButtonProps> = ({ 
  onClick, 
  loading, 
  children = 'Submit', 
  type = 'button', // Default to 'button' to prevent accidental form submits
  className = ""
}) => {
  return (
    <Button 
      type={type}
      onClick={onClick ? () => void onClick() : undefined} 
      className={`cursor-pointer flex items-center gap-2 ${className}`} 
      disabled={loading}
    >
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