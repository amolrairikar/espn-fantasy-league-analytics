import { z } from "zod"

const formSchema = z.object({
  leagueId: z.string().min(1, "Please enter your league ID"),
  platform: z.string().min(1, "Please select a platform"),
  privacy: z.string().min(1, "Please indicate your league privacy settings"),
  oldestSeason: z.string().optional(),
  mostRecentSeason: z.string().optional(),
  swidCookie: z.string().optional(),
  espnS2Cookie: z.string().optional(),
})

type FormValues = z.infer<typeof formSchema>
export type { FormValues }
export const loginSchema = formSchema