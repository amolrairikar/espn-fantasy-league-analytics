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
    espn_s2_cookie: string;
    league_id: string;
    onboarded_date?: string;
    onboarded_status?: boolean;
    privacy: string;
    platform: string;
    seasons: string[];
    swid_cookie: string;
  };
};

type PostLeagueMetadataPayload = {
  league_id: string;
  platform: string;
  privacy: string;
  espn_s2: string;
  swid: string;
  seasons: string[];
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
