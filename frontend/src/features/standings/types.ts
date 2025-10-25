type GetAllTimeStandings = {
  status: string;
  detail: string;
  data: {
    games_played: string;
    losses: string;
    owner_full_name: string;
    points_against_per_game: string;
    points_for_per_game: string;
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
    win_pct: string;
    wins: string;
  }[];
};

type GetLeagueMembers = {
  status: string;
  detail: string;
  data: {
    member_id: string;
    name: string;
  }[];
};

type GetMatchups = {
  status: string;
  detail: string;
  data: {
    loser: string;
    playoff_tier_type: string;
    season: string;
    team_a: string;
    team_a_full_name: string;
    team_a_member_id: string;
    team_a_players: PlayerScoring[];
    team_a_score: string;
    team_a_team_name: string;
    team_b: string;
    team_b_full_name: string;
    team_b_member_id: string;
    team_b_players: PlayerScoring[];
    team_b_score: string;
    team_b_team_name: string;
    week: string;
    winner: string;
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
    win_pct: string;
    wins: string;
  }[];
};

type Matchup = {
  season: number;
  week: number;
  result: string;
  outcome: string;
};

type Member = {
  name: string;
  member_id: string;
};

type MemberConfig = {
  name: string;
  member_id: string;
};

type PlayerScoring = {
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

type StandingsAllTimeBySeason = {
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
  GetLeagueMembers,
  GetMatchups,
  GetSeasonStandings,
  Matchup,
  Member,
  MemberConfig,
  PlayerScoring,
  StandingsAllTime,
  StandingsAllTimeBySeason,
  StandingsH2H,
  StandingsSeason,
};
