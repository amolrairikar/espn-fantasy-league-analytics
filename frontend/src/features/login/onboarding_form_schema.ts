import { z } from "zod"

const yearRegex = /^20\d{2}$/;
const swidRegex = /^\{[0-9A-F]{8}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{4}-[0-9A-F]{12}\}$/i;

const formSchema = z.object({
  leagueId: z.string().trim().min(1, "League ID is required"),
  platform: z.string().min(1, "Please select a platform"),
  oldestSeason: z
    .string()
    .regex(yearRegex, "Must be a valid year (2000 or later)"),
  mostRecentSeason: z
    .string()
    .regex(yearRegex, "Must be a valid year (2000 or later)"),
  swidCookie: z
    .string()
    .trim()
    .regex(swidRegex, "Invalid SWID format (Expected {XXXXXXXX-XXXX-...})"),
  espnS2Cookie: z
    .string()
    .trim()
    .min(32, "ESPN S2 cookie is too short")
}).refine((data) => {
  if (data.oldestSeason && data.mostRecentSeason) {
    return parseInt(data.oldestSeason) <= parseInt(data.mostRecentSeason);
  }
  return true;
}, {
  message: "Oldest season cannot be after the most recent season",
  path: ["oldestSeason"],
});

type OnboardingFormValues = z.infer<typeof formSchema>
export type { OnboardingFormValues }
export const onboardingSchema = formSchema