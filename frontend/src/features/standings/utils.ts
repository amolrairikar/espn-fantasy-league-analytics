export const getOutcomeByOwner = (matchup: any, selectedOwnerId: string): 'W' | 'L' | 'T' => {
  const isHomeOwner = String(matchup.home_team_owner_id) === String(selectedOwnerId);

  const teamId = isHomeOwner ? matchup.home_team_id : matchup.away_team_id;
  
  if (String(matchup.winner) === String(teamId)) {
    return 'W';
  }

  if (
    matchup.winner === null && 
    matchup.home_team_score === matchup.away_team_score &&
    matchup.home_team_score !== null
  ) {
    return 'T';
  }

  return 'L';
};