import { ChampionshipWinners } from '@/features/home/components/ChampionshipWinnersTable';
import { Top10TeamScores } from '@/features/home/components/Top10TeamScoresTable';
import { Top10PlayerScores } from '@/features/home/components/Top10PlayerScoresTable';

export const recordConfigs = [
  {
    key: 'champions',
    label: 'All-Time Champions',
    recordType: 'all_time_championships',
    component: ChampionshipWinners,
  },
  {
    key: 'topTeams',
    label: 'Top 10 Scorers',
    recordType: 'top_10_team_scores',
    component: Top10TeamScores,
    sortOrder: 'desc',
  },
  {
    key: 'bottomTeams',
    label: 'Bottom 10 Scorers',
    recordType: 'bottom_10_team_scores',
    component: Top10TeamScores,
    sortOrder: 'asc',
  },
  { key: 'qb', label: 'Top 10 QB Scorers', recordType: 'top_10_qb_scores', component: Top10PlayerScores },
  { key: 'rb', label: 'Top 10 RB Scorers', recordType: 'top_10_rb_scores', component: Top10PlayerScores },
  { key: 'wr', label: 'Top 10 WR Scorers', recordType: 'top_10_wr_scores', component: Top10PlayerScores },
  { key: 'te', label: 'Top 10 TE Scorers', recordType: 'top_10_te_scores', component: Top10PlayerScores },
  { key: 'dst', label: 'Top 10 D/ST Scorers', recordType: 'top_10_dst_scores', component: Top10PlayerScores },
  { key: 'k', label: 'Top 10 K Scorers', recordType: 'top_10_k_scores', component: Top10PlayerScores },
];
