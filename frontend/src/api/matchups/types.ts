type GetMatchups = {
  detail: string;
  data: {
    season: string;
    week: string;
    playoff_tier_type: string;
    winner: string;
    loser: string;
    team_a_id: string;
    team_a_owner_full_name: string;
    team_a_owner_id: string;
    team_a_team_name: string;
    team_a_score: number;
    team_a_starting_players: {
      player_id: string;
      full_name: string;
      position: string;
      points_scored: number;
    }[];
    team_a_bench_players: {
      player_id: string;
      full_name: string;
      position: string;
      points_scored: number;
    }[];
    team_a_efficiency: number;
    team_b_id: string;
    team_b_owner_full_name: string;
    team_b_owner_id: string;
    team_b_team_name: string;
    team_b_score: number;
    team_b_starting_players: {
      player_id: string;
      full_name: string;
      position: string;
      points_scored: number;
    }[];
    team_b_bench_players: {
      player_id: string;
      full_name: string;
      position: string;
      points_scored: number;
    }[];
    team_b_efficiency: number;
  }[];
};

export type { GetMatchups };
