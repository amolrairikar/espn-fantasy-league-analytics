type GetDraftResults = {
  status: string;
  detail: string;
  data: {
    round: string;
    pick_number: string;
    overall_pick_number: string;
    reserved_for_keeper: boolean;
    bid_amount: string;
    player_id: string;
    player_full_name: string;
    position: string;
    points_scored: number;
    position_rank: number;
    drafted_position_rank: number;
    draft_delta: number;
    owner_id: string;
    owner_full_name: string;
  }[];
};

type ApiDraftResult = GetDraftResults['data'][number];

type DraftResultItem = Omit<ApiDraftResult, 'round' | 'pick_number' | 'overall_pick_number'> & {
  round: number;
  pick_number: number;
  overall_pick_number: number;
};

export type { DraftResultItem, GetDraftResults };