type GetLeagueOnboardingStatus = {
  detail: string;
  data: {
    execution_status: string;
  }
}

type PostLeagueOnboardingPayload = {
  league_id: string;
  platform: string;
  privacy: string;
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
  GetLeagueOnboardingStatus,
  PostLeagueOnboardingPayload,
  PostLeagueOnboardingResponse,
};
