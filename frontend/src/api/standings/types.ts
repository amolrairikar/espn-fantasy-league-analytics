type GetAllTimeStandings = {
  status: string;
  detail: string;
  data: {
    owner_full_name: string;
    games_played: string;
    wins: string;
    losses: string;
    ties: string;
    win_pct: string;
    points_for_per_game: string;
    points_against_per_game: string;
  }[];
};

type GetH2HStandings = {
  status: string;
  detail: string;
  data: {
    owner_full_name: string;
    opponent_full_name: string;
    games_played: string;
    wins: string;
    losses: string;
    ties: string;
    win_pct: string;
    points_for_per_game: string;
    points_against_per_game: string;
  }[];
};

type GetPlayoffStandings = {
  status: string;
  detail: string;
  data: {
    owner_full_name: string;
    games_played: string;
    wins: string;
    losses: string;
    ties: string;
    win_pct: string;
    points_for_per_game: string;
    points_against_per_game: string;
  }[];
}

type GetSeasonStandings = {
  status: string;
  detail: string;
  data: {
    season: string;
    owner_full_name: string;
    wins: string;
    losses: string;
    ties: string;
    win_pct: string;
    points_for: string;
    points_against: string;
    points_differential: string;
    all_play_wins: string;
    all_play_losses: string;
    playoff_status: string;
    championship_status?: string;
  }[];
};

type GetWeeklyStandings = {
  status: string;
  detail: string;
  data: {
    season: string;
    week: string;
    owner_id: string;
    owner_full_name: string;
    wins: string;
    losses: string;
    ties: string;
  }[];
};

export type {
  GetAllTimeStandings,
  GetH2HStandings,
  GetPlayoffStandings,
  GetSeasonStandings,
  GetWeeklyStandings,
};