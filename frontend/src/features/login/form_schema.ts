import { z } from "zod"

const formSchema = z.object({
  leagueId: z.string().min(1, "Please enter your league ID"),
  platform: z.string().min(1, "Please select a platform"),
  oldestSeason: z.string().optional(),
  mostRecentSeason: z.string().optional(),
  swidCookie: z.string().min(1, "Please enter your SWID cookie"),
  espnS2Cookie: z.string().min(1, "Please enter your ESPN S2 cookie"),
})

type FormValues = z.infer<typeof formSchema>
export type { FormValues }
export const loginSchema = formSchema