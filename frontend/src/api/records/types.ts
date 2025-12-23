type GetChampionshipWinners = {
  detail: string;
  data: {
    championships_won: string;
    owner_full_name: string;
    owner_id: string;
  }[];
};

type GetPlayerScores = {
  detail: string;
  data: {
    owner_full_name: string;
    owner_id: string;
    season: string;
    week: string;
    player_name: string;
    points_scored: string;
  }[];
};

type GetTeamScores = {
  detail: string;
  data: {
    owner_full_name: string;
    owner_id: string;
    season: string;
    week: string;
    points_scored: string;
  }[];
};

export type {
  GetChampionshipWinners,
  GetPlayerScores,
  GetTeamScores,
}