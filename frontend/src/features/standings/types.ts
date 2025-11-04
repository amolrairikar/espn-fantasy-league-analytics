type GetAllTimeStandings = {
  status: string;
  detail: string;
  data: {
    games_played: string;
    losses: string;
    owner_full_name: string;
    points_against_per_game: string;
    points_for_per_game: string;
    ties: string;
    win_pct: string;
    wins: string;
  }[];
};

type GetH2HStandings = {
  status: string;
  detail: string;
  data: {
    games_played: string;
    losses: string;
    opponent_full_name: string;
    owner_full_name: string;
    points_against_per_game: string;
    points_for_per_game: string;
    ties: string;
    win_pct: string;
    wins: string;
  }[];
};

type GetSeasonStandings = {
  status: string;
  detail: string;
  data: {
    losses: string;
    owner_full_name: string;
    points_against_per_game: string;
    points_for_per_game: string;
    season: string;
    ties: string;
    win_pct: string;
    wins: string;
  }[];
};

type GetWeeklyStandings = {
  status: string;
  detail: string;
  data: {
    losses: string;
    owner_full_name: string;
    season: string;
    team_member_id: string;
    ties: string;
    week: string;
    win_pct: string;
    wins: string;
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
    loser: string;
    playoff_tier_type: string;
    season: string;
    team_a: string;
    team_a_full_name: string;
    team_a_member_id: string;
    team_a_players: PlayerScoringDetails[];
    team_a_score: string;
    team_a_team_name: string;
    team_b: string;
    team_b_full_name: string;
    team_b_member_id: string;
    team_b_players: PlayerScoringDetails[];
    team_b_score: string;
    team_b_team_name: string;
    week: string;
    winner: string;
  }[];
};

type MatchupTableView = {
  season: number;
  week: number;
  opponent_full_name?: string;
  result: string;
  outcome: string;
};

type Member = {
  name: string;
  member_id: string;
};

type PlayerScoringDetails = {
  player_id: string;
  full_name: string;
  position: string;
  points_scored: string;
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
  points_for_per_game: number;
  points_against_per_game: number;
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
