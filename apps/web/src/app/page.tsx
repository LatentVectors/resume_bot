"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { useCreateJob } from "@/lib/hooks/useJobMutations";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useExperiences } from "@/lib/hooks/useExperiences";
import { Alert, AlertDescription } from "@/components/ui/alert";

const jobDescriptionSchema = z.object({
  description: z.string().min(1, "Job description is required"),
});

type JobDescriptionFormData = z.infer<typeof jobDescriptionSchema>;

export default function Home() {
  const router = useRouter();
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Fetch current user
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();

  // Fetch experiences to check if user has any
  const { data: experiences, isLoading: isLoadingExperiences } = useExperiences(
    user?.id ?? 0
  );

  // Create job mutation
  const createJob = useCreateJob();

  const form = useForm<JobDescriptionFormData>({
    resolver: zodResolver(jobDescriptionSchema),
    defaultValues: {
      description: "",
    },
  });

  const onSubmit = async (data: JobDescriptionFormData) => {
    if (!user?.id) {
      return;
    }

    setIsSubmitting(true);
    try {
      // Create job with just description (title/company will be filled in Step 1)
      const newJob = await createJob.mutateAsync({
        user_id: user.id,
        data: {
          description: data.description.trim(),
          title: null,
          company: null,
          favorite: false,
        },
      });

      // Navigate to intake flow Step 1
      router.push(`/intake/${newJob.id}/details`);
    } catch (error) {
      console.error("Failed to create job:", error);
      // Error will be handled by TanStack Query
    } finally {
      setIsSubmitting(false);
    }
  };

  const hasNoExperiences =
    !isLoadingExperiences && (!experiences || experiences.length === 0);

  if (isLoadingUser) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-muted-foreground">Loading...</div>
      </div>
    );
  }

  if (!user) {
    return (
      <div className="flex min-h-[60vh] items-center justify-center">
        <div className="text-destructive">
          Unable to load user. Please refresh the page.
        </div>
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl">
      <Card>
        <CardHeader>
          <CardTitle>Save Job</CardTitle>
          <CardDescription>
            Enter a job description to start the intake workflow. You&apos;ll be
            able to add title and company details in the next step.
          </CardDescription>
        </CardHeader>
        <CardContent>
          {hasNoExperiences && (
            <Alert className="mb-6">
              <AlertDescription>
                You don&apos;t have any experiences yet. Consider adding
                experiences in your{" "}
                <Link href="/profile" className="underline">
                  profile
                </Link>{" "}
                before starting the intake workflow.
              </AlertDescription>
            </Alert>
          )}

          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
              <FormField
                control={form.control}
                name="description"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Job Description</FormLabel>
                    <FormControl>
                      <Textarea
                        {...field}
                        placeholder="Enter your job description, skills, or any other requirements..."
                        className="min-h-[400px] resize-y"
                      />
                    </FormControl>
                    <FormDescription>
                      Paste the full job description, requirements, or any
                      relevant details about the position.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="flex justify-end">
                <Button
                  type="submit"
                  disabled={isSubmitting || createJob.isPending}
                >
                  {isSubmitting || createJob.isPending
                    ? "Saving..."
                    : "Save Job"}
                </Button>
              </div>
            </form>
          </Form>
        </CardContent>
      </Card>
    </div>
  );
}
