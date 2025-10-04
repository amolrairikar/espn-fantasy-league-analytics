import type { LeagueData } from '@/components/types/league_data';

type HeaderProps = {
  leagueData: LeagueData | null;
  onLogout: () => void;
};

export type { HeaderProps };
