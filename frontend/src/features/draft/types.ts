type DraftResults = {
    round: string;
    round_pick_number: string;
    overall_pick_number: string;
    reserved_for_keeper: boolean;
    bid_amount: string;
    player_id: string;
    player_full_name: string;
    position: string;
    points_scored: number;
    position_rank: number;
    position_draft_rank: number;
    owner_id: string;
    owner_full_name: string;
    season: string;
    draft_delta: number;
};

type DraftResultItem = Omit<DraftResults, 'round' | 'pick_number' | 'overall_pick_number'> & {
  round: number;
  pick_number: number;
  overall_pick_number: number;
};

export type { DraftResultItem, DraftResults };