type PostLeagueOnboardingPayload = {
  league_id: string;
  platform: string;
  privacy: string;
  espn_s2: string;
  swid: string;
  seasons: string[];
  onboarded_status?: boolean;
  onboarded_date?: string;
};

type PostLeagueOnboardingResponse = {
  status: string;
  detail: string;
  data: {
    execution_id: string;
  };
};

type GetLeagueOnboardingStatus = {
  status: string;
  detail: string;
  data: {
    execution_status: string;
  };
};

type PollOptions<T> = {
  interval: number; // time between polls in ms
  timeout?: number; // maximum time to poll in ms
  validate: (result: T) => boolean; // function to check if polling should stop
};

export type { PostLeagueOnboardingPayload, PostLeagueOnboardingResponse, GetLeagueOnboardingStatus, PollOptions };
