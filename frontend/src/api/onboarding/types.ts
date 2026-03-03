type PostLeagueOnboardingPayload = {
  league_id: string;
  platform: string;
  espn_s2: string;
  swid: string;
  seasons: string[];
}

type PostLeagueOnboardingResponse = {
  detail: string;
  data: {
    execution_id: string;
  };
};

export type {
  PostLeagueOnboardingPayload,
  PostLeagueOnboardingResponse,
};
