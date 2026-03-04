export type Matchup = {
  home_team_id: string;
  home_team_score: number;
  home_team_starting_players: PlayerScoringDetails[];
  home_team_bench_players: PlayerScoringDetails[]; 
  home_team_efficiency: number;
  home_team_full_name: string;
  home_team_team_name: string;
  home_team_owner_id: string;
  away_team_id: string;
  away_team_score: number;
  away_team_starting_players: PlayerScoringDetails[];
  away_team_bench_players: PlayerScoringDetails[]; 
  away_team_efficiency: number;
  away_team_full_name: string;
  away_team_team_name: string;
  away_team_owner_id: string;
  playoff_tier_type: string;
  winner: string;
  loser: string;
  matchup_week: string;
  season: string;
};

export type PlayerScoringDetails = {
  player_id: string;
  full_name: string;
  points_scored: number;
  position: string;
};