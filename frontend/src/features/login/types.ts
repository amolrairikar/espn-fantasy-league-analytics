type ValidateLeagueReponse = {
  status: string;
  detail: string;
};

type LeagueData = {
  leagueId: string;
  platform: string;
};

type GetLeagueMetadata = {
  status: string;
  detail: string;
  data: {
    league_id: string;
    privacy: string;
    platform: string;
    swid_cookie: string;
    espn_s2_cookie: string;
    seasons: string[];
    onboarded_date?: string;
    onboarded_status?: string;
    PK: string;
    SK: string;
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

export type {
  GetLeagueMetadata,
  ValidateLeagueReponse,
  PostLeagueMetadataPayload,
  PostLeagueMetadataResponse,
  LeagueData,
};
