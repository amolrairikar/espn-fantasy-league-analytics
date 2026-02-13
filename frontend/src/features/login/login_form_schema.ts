import { z } from "zod"


const formSchema = z.object({
  leagueId: z.string().trim().min(1, "League ID is required"),
  platform: z.string().min(1, "Please select a platform")
});

type LoginFormValues = z.infer<typeof formSchema>
export type { LoginFormValues }
export const loginFormSchema = formSchema