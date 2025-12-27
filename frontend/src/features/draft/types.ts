import type { GetDraftResults } from "@/api/draft_results/types";

type ApiDraftResult = GetDraftResults['data'][number];

type DraftResultItem = Omit<ApiDraftResult, 'round' | 'pick_number' | 'overall_pick_number'> & {
  round: number;
  pick_number: number;
  overall_pick_number: number;
};

export type { DraftResultItem };