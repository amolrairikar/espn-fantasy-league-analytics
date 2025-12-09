import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/card";
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";
import type { DraftResultItem } from '@/features/draft/types';

interface DraftPickCardProps {
  pick: DraftResultItem;
};

const positionColors: Record<string, string> = {
  "QB": "#C05E85",
  "RB": "#73C3A6",
  "WR": "#46A2CB",
  "TE": "#CC8C4C",
  "D/ST": "#9A5F50",
  "K": "#9295D0",
};

function DraftPickCard({ pick }: DraftPickCardProps) {
  const bgColor = positionColors[pick.position] || "#FFFFFF";
  return (
    <Card 
      className="mb-3 shadow-sm rounded-2xl h-35 w-50 flex flex-col justify-center px-4 py-4"
      style={{ backgroundColor: bgColor }}
    >

      <CardHeader className="flex justify-center">
        <CardTitle className="font-semibold text-center text-black line-clamp-3 leading-tight min-h-[3.6rem] flex items-center">
          {pick.player_full_name}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex flex-row justify-between items-center text-sm text-black px-1 w-full">

        {/* Left side */}
        <div className="flex flex-col space-y-1 items-start">
          <p>{pick.position}</p>
          <p>{pick.round}.{pick.pick_number}</p>
        </div>

        {/* Right side: draft_delta pill */}
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <div
                className={`
                  px-2 py-1 rounded-full font-semibold text-xs shrink-0 cursor-default
                  ${pick.draft_delta > 5 ? "bg-green-500 text-white" : ""}
                  ${pick.draft_delta < -5 ? "bg-red-500 text-white" : ""}
                  ${pick.draft_delta >= -5 && pick.draft_delta <= 5 ? "bg-gray-200 text-black" : ""}
                `}
              >
                {pick.draft_delta > 0 ? `+${pick.draft_delta}` : pick.draft_delta}
              </div>
            </TooltipTrigger>

            <TooltipContent>
              <p><span className="font-semibold">Drafted As:</span> {pick.position}{pick.drafted_position_rank}</p>
              <p><span className="font-semibold">Finished As:</span> {pick.position}{pick.position_rank}</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>

      </CardContent>

    </Card>
  );
}

export default DraftPickCard;
