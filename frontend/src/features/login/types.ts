type LeagueData = {
  leagueId: string;
  platform: string;
};

type LoginProps = {
  onLoginSuccess: (data: LeagueData) => void;
};

export type {
  LeagueData,
  LoginProps,
};
