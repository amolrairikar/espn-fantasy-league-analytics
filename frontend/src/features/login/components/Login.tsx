import { useState } from 'react';
import { LoginForm } from '@/features/login/components/LoginForm';
import { OnboardDialog } from '@/features/login/components/OnboardDialog';
import type { LoginProps } from '@/api/league_metadata/types';

function Login({ onLoginSuccess }: LoginProps) {
  const [showOnboardDialog, setShowOnboardDialog] = useState(false);
  const [initialData, setInitialData] = useState({ leagueId: '', platform: 'ESPN' });

  const handleOpenOnboard = (leagueId: string, platform: string) => {
    setInitialData({ leagueId, platform });
    setShowOnboardDialog(true);
  };

  return (
    <div className="space-y-6">
      <LoginForm 
        onLoginSuccess={onLoginSuccess} 
        onNotFound={handleOpenOnboard} 
      />

      <OnboardDialog 
        open={showOnboardDialog} 
        onOpenChange={setShowOnboardDialog}
        initialData={initialData}
        onLoginSuccess={onLoginSuccess}
      />
    </div>
  );
}

export default Login;