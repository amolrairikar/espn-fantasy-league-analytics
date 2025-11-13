type GetChampionshipWinners = {
  detail: string;
  data: {
    championships_won: string;
    owner_full_name: string;
    owner_member_id: string;
  }[];
};

type GetPlayerScores = {
  detail: string;
  data: {
    member_id: string;
    owner_full_name: string;
    player_name: string;
    points_scored: string;
    position: string;
    season: string;
    week: string;
  }[];
};

type GetTeamScores = {
  detail: string;
  data: {
    member_id: string;
    owner_full_name: string;
    score: string;
    season: string;
    week: string;
  }[];
};

type OnboardResponse = { execution_id: string };

type OnboardStatusResponse = { execution_status: string };

type PostLeagueOnboardingPayload = {
  league_id: string;
  platform: string;
  privacy: string;
  espn_s2: string;
  swid: string;
  seasons: string[];
};

type PutLeagueMetadataPayload = {
  league_id: string;
  platform: string;
  privacy: string;
  espn_s2: string;
  swid: string;
  seasons: string[];
  onboarded_status: boolean;
  onboarded_date: string;
};

type PollOptions<T> = {
  interval: number; // time between polls in ms
  timeout?: number; // maximum time to poll in ms
  validate: (result: T) => boolean; // function to check if polling should stop
};

export type {
  GetChampionshipWinners,
  GetPlayerScores,
  GetTeamScores,
  OnboardResponse,
  OnboardStatusResponse,
  PutLeagueMetadataPayload,
  PostLeagueOnboardingPayload,
  PollOptions,
};
