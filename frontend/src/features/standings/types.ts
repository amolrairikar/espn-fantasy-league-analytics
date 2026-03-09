export type AllTimeStandingsData = {
  owner_id: string;
  owner_name: string;
  games_played: string;
  wins: number;
  losses: number;
  ties: number;
  record: string;
  win_pct: number;
  avg_pf: number;
  avg_pa: number;
}

export type H2HStandingsData = {
  owner_id: string;
  owner_name: string;
  opponent_id: string;
  opponent_name: string;
  matchups: string;
  wins: number;
  losses: number;
  ties: number;
  record: string;
  win_pct: number;
  total_pf: number;
  total_pa: number;
  avg_pf: number;
  avg_pa: number;
}

export type RegularSeasonStandingsData = {
  season: string;
  owner_id: string;
  owner_name: string;
  games_played: string;
  wins: number;
  losses: number;
  ties: number;
  record: string;
  win_pct: number;
  total_pf: number;
  total_pa: number;
  avg_pf: number;
  avg_pa: number;
  total_vs_league_wins: number;
  total_vs_league_losses: number;
  playoff_status: string;
  championship_status: string;
}

export type MatchupTableView = {
  season: string;
  week: number;
  opponent_full_name?: string;
  result: string;
  outcome: string;
};