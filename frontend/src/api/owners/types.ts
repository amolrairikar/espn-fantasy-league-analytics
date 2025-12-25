type GetLeagueOwners = {
  status: string;
  detail: string;
  data: {
    owner_full_name: string;
    owner_id: string;
  }[];
};

export type { GetLeagueOwners };
