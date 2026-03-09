import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";
import { Progress } from "@/components/ui/progress";

interface ProgressDialogProps {
  isOpen: boolean;
  title?: string;
  description?: string;
  text: string; // The dynamic text prop
  maxTimeInSeconds: number; // Duration to reach 99%
  isCompleting?: boolean;
}

export function ProgressDialog({
  isOpen,
  title = "Processing...",
  description,
  text,
  maxTimeInSeconds,
  isCompleting = false
}: ProgressDialogProps) {
  const [progress, setProgress] = useState(0);

  useEffect(() => {
    if (!isOpen) {
      setProgress(0);
      return;
    }

    // --- PRIORITY 1: Force Complete ---
    if (isCompleting) {
      setProgress(99);
      return; // Stop animation loop entirely
    }

    // --- PRIORITY 2: Linear Animation ---
    const startTime = Date.now();
    const durationMs = maxTimeInSeconds * 1000;
    const targetProgress = 99;

    let animationFrame: number;

    const updateProgress = () => {
      const elapsed = Date.now() - startTime;
      const percentage = Math.min((elapsed / durationMs) * targetProgress, targetProgress);

      setProgress(percentage);

      if (percentage < targetProgress) {
        animationFrame = requestAnimationFrame(updateProgress);
      }
    };

    animationFrame = requestAnimationFrame(updateProgress);

    return () => {
      if (animationFrame) cancelAnimationFrame(animationFrame);
    };
  }, [isOpen, maxTimeInSeconds, isCompleting]); // isCompleting triggers a re-run of this logic

  return (
    <Dialog open={isOpen}>
      <DialogContent className="sm:max-w-md" onPointerDownOutside={(e) => e.preventDefault()}>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        
        <div className="py-6 space-y-4">
          <Progress 
            value={progress} 
            className="w-full transition-all duration-300 ease-in-out" 
          />
          <p className="text-sm text-center text-muted-foreground animate-pulse">
            {text} ({Math.round(progress)}%)
          </p>
        </div>
      </DialogContent>
    </Dialog>
  );
}