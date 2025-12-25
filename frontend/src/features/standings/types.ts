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

type GetLeagueMembers = {
  status: string;
  detail: string;
  data: Member[];
};

type GetMatchupsBetweenTeams = {
  status: string;
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
    team_a_score: string;
    team_a_players: PlayerScoringDetails[];
    team_b_id: string;
    team_b_owner_full_name: string;
    team_b_owner_id: string;
    team_b_team_name: string;
    team_b_score: string;
    team_b_players: PlayerScoringDetails[];
  }[];
};

type MatchupTableView = {
  season: string;
  week: number;
  opponent_full_name?: string;
  result: string;
  outcome: string;
};

type Member = {
  owner_full_name: string;
  owner_id: string;
};

type PlayerScoringDetails = {
  player_id: string;
  full_name: string;
  position: string;
  points_scored: number;
};

type StandingsAllTime = {
  owner_full_name: string;
  games_played: number;
  record: string;
  win_pct: number;
  points_for_per_game: number;
  points_against_per_game: number;
};

type StandingsAllTimeBySeasonGraphView = {
  season: string;
  wins: string;
};

type StandingsH2H = {
  owner_full_name: string;
  opponent_full_name: string;
  games_played: number;
  record: string;
  win_pct: number;
  points_for_per_game: number;
  points_against_per_game: number;
};

type StandingsSeason = {
  owner_full_name: string;
  record: string;
  win_pct: number;
  points_for: number;
  points_against: number;
  points_differential: number;
  playoff_status: string;
  championship_status?: string;
};

export type {
  GetAllTimeStandings,
  GetH2HStandings,
  GetSeasonStandings,
  GetWeeklyStandings,
  GetLeagueMembers,
  GetMatchupsBetweenTeams,
  MatchupTableView,
  Member,
  PlayerScoringDetails,
  StandingsAllTime,
  StandingsAllTimeBySeasonGraphView,
  StandingsH2H,
  StandingsSeason,
};
