"use client";

import { useState } from "react";
import { Plus } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { ExperienceCard } from "@/components/profile/ExperienceCard";
import { EducationCard } from "@/components/profile/EducationCard";
import { CertificateCard } from "@/components/profile/CertificateCard";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useExperiences } from "@/lib/hooks/useExperiences";
import { useEducation } from "@/lib/hooks/useEducation";
import { useCertificates } from "@/lib/hooks/useCertificates";
import { useCreateExperience } from "@/lib/hooks/useExperienceMutations";
import { useCreateEducation } from "@/lib/hooks/useEducationMutations";
import { useCreateCertificate } from "@/lib/hooks/useCertificateMutations";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";

const experienceSchema = z.object({
  company_name: z.string().min(1, "Company name is required"),
  job_title: z.string().min(1, "Job title is required"),
  location: z.string().optional(),
  start_date: z.string().min(1, "Start date is required"),
  end_date: z.string().optional(),
  company_overview: z.string().optional(),
  role_overview: z.string().optional(),
  skills: z.string().optional(),
});

type ExperienceFormData = z.infer<typeof experienceSchema>;

export default function ProfilePage() {
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();
  const { data: experiences, isLoading: isLoadingExperiences } = useExperiences(
    user?.id ?? 0
  );
  const { data: education, isLoading: isLoadingEducation } = useEducation(
    user?.id ?? 0
  );
  const { data: certificates, isLoading: isLoadingCertificates } = useCertificates(
    user?.id ?? 0
  );

  const [showAddExperienceDialog, setShowAddExperienceDialog] = useState(false);
  const [showAddEducationDialog, setShowAddEducationDialog] = useState(false);
  const [showAddCertificateDialog, setShowAddCertificateDialog] = useState(false);

  const createExperience = useCreateExperience();
  const createEducation = useCreateEducation();
  const createCertificate = useCreateCertificate();

  const experienceForm = useForm<ExperienceFormData>({
    resolver: zodResolver(experienceSchema),
    defaultValues: {
      company_name: "",
      job_title: "",
      location: "",
      start_date: "",
      end_date: "",
      company_overview: "",
      role_overview: "",
      skills: "",
    },
  });

  const onAddExperience = async (data: ExperienceFormData) => {
    if (!user?.id) return;
    try {
      await createExperience.mutateAsync({
        user_id: user.id,
        data: {
          company_name: data.company_name,
          job_title: data.job_title,
          location: data.location || null,
          start_date: data.start_date,
          end_date: data.end_date || null,
          company_overview: data.company_overview || null,
          role_overview: data.role_overview || null,
          skills: data.skills
            ? data.skills.split(",").map((s) => s.trim()).filter(Boolean)
            : null,
        },
      });
      setShowAddExperienceDialog(false);
      experienceForm.reset();
    } catch (error) {
      console.error("Failed to create experience:", error);
    }
  };

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
    <div className="mx-auto max-w-4xl space-y-8">
      {/* User Information */}
      <Card>
        <CardHeader>
          <CardTitle>Profile Information</CardTitle>
          <CardDescription>Your personal information</CardDescription>
        </CardHeader>
        <CardContent className="space-y-2">
          <div>
            <span className="text-sm font-medium">Name: </span>
            <span className="text-sm text-muted-foreground">
              {user.first_name} {user.last_name}
            </span>
          </div>
          {user.email && (
            <div>
              <span className="text-sm font-medium">Email: </span>
              <span className="text-sm text-muted-foreground">{user.email}</span>
            </div>
          )}
          {user.phone_number && (
            <div>
              <span className="text-sm font-medium">Phone: </span>
              <span className="text-sm text-muted-foreground">{user.phone_number}</span>
            </div>
          )}
          {(user.city || user.state) && (
            <div>
              <span className="text-sm font-medium">Location: </span>
              <span className="text-sm text-muted-foreground">
                {[user.city, user.state].filter(Boolean).join(", ")}
              </span>
            </div>
          )}
          {user.linkedin_url && (
            <div>
              <span className="text-sm font-medium">LinkedIn: </span>
              <a
                href={user.linkedin_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline"
              >
                {user.linkedin_url}
              </a>
            </div>
          )}
          {user.github_url && (
            <div>
              <span className="text-sm font-medium">GitHub: </span>
              <a
                href={user.github_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-sm text-primary hover:underline"
              >
                {user.github_url}
              </a>
            </div>
          )}
        </CardContent>
      </Card>

      {/* Experiences Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Work Experience</CardTitle>
              <CardDescription>Your professional work experience</CardDescription>
            </div>
            <Button
              onClick={() => {
                experienceForm.reset();
                setShowAddExperienceDialog(true);
              }}
            >
              <Plus className="mr-2 size-4" />
              Add Experience
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoadingExperiences ? (
            <div className="text-center text-muted-foreground">Loading experiences...</div>
          ) : experiences && experiences.length > 0 ? (
            experiences.map((experience) => (
              <ExperienceCard
                key={experience.id}
                experience={experience}
                userId={user.id}
              />
            ))
          ) : (
            <div className="text-center text-muted-foreground">
              No experiences yet. Click &quot;Add Experience&quot; to get started.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Education Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Education</CardTitle>
              <CardDescription>Your educational background</CardDescription>
            </div>
            <Button
              onClick={() => {
                setShowAddEducationDialog(true);
              }}
            >
              <Plus className="mr-2 size-4" />
              Add Education
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoadingEducation ? (
            <div className="text-center text-muted-foreground">Loading education...</div>
          ) : education && education.length > 0 ? (
            education.map((edu) => (
              <EducationCard key={edu.id} education={edu} userId={user.id} />
            ))
          ) : (
            <div className="text-center text-muted-foreground">
              No education entries yet. Click &quot;Add Education&quot; to get started.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Certificates Section */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>Certificates</CardTitle>
              <CardDescription>Your professional certifications</CardDescription>
            </div>
            <Button
              onClick={() => {
                setShowAddCertificateDialog(true);
              }}
            >
              <Plus className="mr-2 size-4" />
              Add Certificate
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {isLoadingCertificates ? (
            <div className="text-center text-muted-foreground">Loading certificates...</div>
          ) : certificates && certificates.length > 0 ? (
            certificates.map((cert) => (
              <CertificateCard key={cert.id} certificate={cert} userId={user.id} />
            ))
          ) : (
            <div className="text-center text-muted-foreground">
              No certificates yet. Click &quot;Add Certificate&quot; to get started.
            </div>
          )}
        </CardContent>
      </Card>

      {/* Add Experience Dialog */}
      <Dialog open={showAddExperienceDialog} onOpenChange={setShowAddExperienceDialog}>
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Add Experience</DialogTitle>
            <DialogDescription>
              Add a new work experience entry.
            </DialogDescription>
          </DialogHeader>
          <Form {...experienceForm}>
            <form
              onSubmit={experienceForm.handleSubmit(onAddExperience)}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={experienceForm.control}
                  name="company_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Company Name *</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={experienceForm.control}
                  name="job_title"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Job Title *</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={experienceForm.control}
                name="location"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Location</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={experienceForm.control}
                  name="start_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Start Date *</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={experienceForm.control}
                  name="end_date"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>End Date</FormLabel>
                      <FormControl>
                        <Input type="date" {...field} />
                      </FormControl>
                      <FormDescription>Leave empty for current position</FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={experienceForm.control}
                name="company_overview"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Company Overview</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={experienceForm.control}
                name="role_overview"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role Overview</FormLabel>
                    <FormControl>
                      <Textarea {...field} rows={3} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={experienceForm.control}
                name="skills"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Skills</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="e.g., Python, SQL, Project Management" />
                    </FormControl>
                    <FormDescription>Separate skills with commas</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowAddExperienceDialog(false);
                    experienceForm.reset();
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={createExperience.isPending}>
                  {createExperience.isPending ? "Adding..." : "Add Experience"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Add Education Dialog */}
      {showAddEducationDialog && (
        <EducationCard
          education={null}
          userId={user.id}
          onAdd={() => setShowAddEducationDialog(false)}
        />
      )}

      {/* Add Certificate Dialog */}
      {showAddCertificateDialog && (
        <CertificateCard
          certificate={null}
          userId={user.id}
          onAdd={() => setShowAddCertificateDialog(false)}
        />
      )}
    </div>
  );
}

