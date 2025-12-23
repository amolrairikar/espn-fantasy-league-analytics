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
    team_a_players: {
      player_id: string;
      player_full_name: string;
      position: string;
      points_scored: number;
    };
    team_b_id: string;
    team_b_owner_full_name: string;
    team_b_owner_id: string;
    team_b_team_name: string;
    team_b_score: number;
    team_b_players: {
      player_id: string;
      player_full_name: string;
      position: string;
      points_scored: number;
    };
  };
};

export type { GetMatchups };
