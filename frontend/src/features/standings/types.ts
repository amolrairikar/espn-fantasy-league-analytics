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

type Team = {
  owner_full_name: string;
  opponent_full_name?: string;
  games_played?: number;
  wins: number;
  losses: number;
  win_pct: number;
  points_for_per_game: number;
  points_against_per_game: number;
};

type Matchup = {
  season: string;
  week: string;
  result: string;
  outcome: string;
};

type Member = {
  PK: string;
  SK: string;
  name: string;
  member_id: string;
};

export type {
  GetAllTimeStandings,
  GetH2HStandings,
  GetLeagueMembers,
  GetMatchups,
  GetSeasonStandings,
  Matchup,
  Member,
  Team,
};
