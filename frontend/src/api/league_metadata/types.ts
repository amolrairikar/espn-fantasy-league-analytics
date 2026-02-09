type ValidateLeagueReponse = {
  detail: string;
};

type LeagueData = {
  leagueId: string;
  platform: string;
};

type GetLeagueMetadata = {
  detail: string;
  data: {
    league_id: string;
    platform: string;
    espn_s2_cookie: string;
    swid_cookie: string;
    seasons: string[];
    onboarded_status?: boolean;
    onboarded_date?: string;
  };
};

type PostLeagueMetadataPayload = {
  league_id: string;
  platform: string;
  espn_s2: string;
  swid: string;
  seasons: string[];
  onboarded_date?: string;
  onboarded_status?: boolean;
};

type PostLeagueMetadataResponse = {
  status: string;
  detail: string;
  data: {
    league_id: string;
  };
};

type LoginProps = {
  onLoginSuccess: (data: LeagueData) => void;
};

export type {
  GetLeagueMetadata,
  LeagueData,
  LoginProps,
  PostLeagueMetadataPayload,
  PostLeagueMetadataResponse,
  ValidateLeagueReponse,
};
