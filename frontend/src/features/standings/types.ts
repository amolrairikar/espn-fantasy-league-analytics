type GetAllTimeStandings = {
  status: string;
  detail: string;
  data: {
    PK: string;
    SK: string;
    owner_full_name: string;
    games_played: string;
    wins: string;
    losses: string;
    win_pct: string;
    points_for_per_game: string;
    points_against_per_game: string;
  }[];
};

type GetAllTimeStandingsBySeason = {
  status: string;
  detail: string;
  data: {
    PK: string;
    SK: string;
    GSI2PK: string;
    GSI2SK: string;
    season: string;
    owner_full_name: string;
    games_played: string;
    wins: string;
    losses: string;
    win_pct: string;
    points_for_per_game: string;
    points_against_per_game: string;
  }[];
};

type GetH2HStandings = {
  status: string;
  detail: string;
  data: {
    PK: string;
    SK: string;
    owner_full_name: string;
    opponent_full_name: string;
    games_played: string;
    wins: string;
    losses: string;
    win_pct: string;
    points_for_per_game: string;
    points_against_per_game: string;
  }[];
};

type GetLeagueMembers = {
  status: string;
  detail: string;
  data: {
    PK: string;
    SK: string;
    member_id: string;
    name: string;
  }[];
};

type GetMatchups = {
  status: string;
  detail: string;
  data: {
    PK: string;
    SK: string;
    GSI1PK: string;
    GSI1SK: string;
    team_a: string;
    team_a_member_id: string;
    team_a_score: string;
    team_b: string;
    team_b_member_id: string;
    team_b_score: string;
    season: string;
    week: string;
    winner: string;
    loser: string;
    playoff_tier_type: string;
  }[];
};

type GetSeasonStandings = {
  status: string;
  detail: string;
  data: {
    PK: string;
    SK: string;
    owner_full_name: string;
    season: string;
    wins: string;
    losses: string;
    win_pct: string;
    points_for_per_game: string;
    points_against_per_game: string;
  }[];
};

type Matchup = {
  season: number;
  week: number;
  result: string;
  outcome: string;
};

type Member = {
  PK: string;
  SK: string;
  name: string;
  member_id: string;
};

type MemberConfig = {
  name: string;
  member_id: string;
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
  GetAllTimeStandingsBySeason,
  GetH2HStandings,
  GetLeagueMembers,
  GetMatchups,
  GetSeasonStandings,
  Matchup,
  Member,
  MemberConfig,
  StandingsAllTime,
  StandingsAllTimeBySeason,
  StandingsH2H,
  StandingsSeason,
};
