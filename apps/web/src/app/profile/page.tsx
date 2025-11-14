"use client";

import { useState, useEffect } from "react";
import { Plus, Edit, Linkedin, Github } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { ExperienceCard } from "@/components/profile/ExperienceCard";
import { EducationCard } from "@/components/profile/EducationCard";
import { CertificateCard } from "@/components/profile/CertificateCard";
import { useCurrentUser } from "@/lib/hooks/useUser";
import { useUpdateUser } from "@/lib/hooks/useUserMutations";
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

const userProfileSchema = z.object({
  first_name: z.string().min(1, "First name is required"),
  last_name: z.string().min(1, "Last name is required"),
  email: z.string().email("Invalid email address").optional().or(z.literal("")),
  phone_number: z.string().optional(),
  city: z.string().optional(),
  state: z.string().optional(),
  linkedin_url: z
    .string()
    .url("Invalid URL")
    .optional()
    .or(z.literal(""))
    .refine(
      (val) => !val || val.includes("linkedin.com"),
      "Must be a LinkedIn URL"
    ),
  github_url: z
    .string()
    .url("Invalid URL")
    .optional()
    .or(z.literal(""))
    .refine(
      (val) => !val || val.includes("github.com"),
      "Must be a GitHub URL"
    ),
});

type ExperienceFormData = z.infer<typeof experienceSchema>;
type UserProfileFormData = z.infer<typeof userProfileSchema>;

export default function ProfilePage() {
  const { data: user, isLoading: isLoadingUser } = useCurrentUser();
  const { data: experiences, isLoading: isLoadingExperiences } = useExperiences(
    user?.id ?? 0
  );
  const { data: education, isLoading: isLoadingEducation } = useEducation(
    user?.id ?? 0
  );
  const { data: certificates, isLoading: isLoadingCertificates } =
    useCertificates(user?.id ?? 0);

  const [showAddExperienceDialog, setShowAddExperienceDialog] = useState(false);
  const [showAddEducationDialog, setShowAddEducationDialog] = useState(false);
  const [showAddCertificateDialog, setShowAddCertificateDialog] =
    useState(false);
  const [showEditProfileDialog, setShowEditProfileDialog] = useState(false);

  const updateUser = useUpdateUser();
  const createExperience = useCreateExperience();

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

  const userProfileForm = useForm<UserProfileFormData>({
    resolver: zodResolver(userProfileSchema),
    defaultValues: {
      first_name: user?.first_name || "",
      last_name: user?.last_name || "",
      email: user?.email || "",
      phone_number: user?.phone_number || "",
      city: user?.city || "",
      state: user?.state || "",
      linkedin_url: user?.linkedin_url || "",
      github_url: user?.github_url || "",
    },
  });

  // Update form when user data changes
  useEffect(() => {
    if (user) {
      userProfileForm.reset({
        first_name: user.first_name,
        last_name: user.last_name,
        email: user.email || "",
        phone_number: user.phone_number || "",
        city: user.city || "",
        state: user.state || "",
        linkedin_url: user.linkedin_url || "",
        github_url: user.github_url || "",
      });
    }
  }, [user, userProfileForm]);

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
            ? data.skills
                .split(",")
                .map((s) => s.trim())
                .filter(Boolean)
            : undefined,
        },
      });
      setShowAddExperienceDialog(false);
      experienceForm.reset();
    } catch (error) {
      console.error("Failed to create experience:", error);
    }
  };

  const onUpdateProfile = async (data: UserProfileFormData) => {
    if (!user?.id) return;
    try {
      await updateUser.mutateAsync({
        userId: user.id,
        data: {
          first_name: data.first_name,
          last_name: data.last_name,
          email: data.email || null,
          phone_number: data.phone_number || null,
          city: data.city || null,
          state: data.state || null,
          linkedin_url: data.linkedin_url || null,
          github_url: data.github_url || null,
        },
      });
      setShowEditProfileDialog(false);
    } catch (error) {
      console.error("Failed to update profile:", error);
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
      <div className="space-y-4">
        <h2 className="text-2xl font-semibold tracking-tight">
          Profile Information
        </h2>
        <Card>
          <CardContent className="pt-4 space-y-2 relative">
            <Button
              variant="ghost"
              size="sm"
              className="absolute top-4 right-4"
              onClick={() => {
                userProfileForm.reset({
                  first_name: user.first_name,
                  last_name: user.last_name,
                  email: user.email || "",
                  phone_number: user.phone_number || "",
                  city: user.city || "",
                  state: user.state || "",
                  linkedin_url: user.linkedin_url || "",
                  github_url: user.github_url || "",
                });
                setShowEditProfileDialog(true);
              }}
            >
              <Edit className="size-4" />
            </Button>
            <div>
              <span className="text-sm font-medium">Name: </span>
              <span className="text-sm text-muted-foreground">
                {user.first_name || "Not provided"} {user.last_name || ""}
              </span>
            </div>
            <div>
              <span className="text-sm font-medium">Email: </span>
              <span className="text-sm text-muted-foreground">
                {user.email || "Not provided"}
              </span>
            </div>
            <div>
              <span className="text-sm font-medium">Phone: </span>
              <span className="text-sm text-muted-foreground">
                {user.phone_number || "Not provided"}
              </span>
            </div>
            <div>
              <span className="text-sm font-medium">Location: </span>
              <span className="text-sm text-muted-foreground">
                {[user.city, user.state].filter(Boolean).join(", ") ||
                  "Not provided"}
              </span>
            </div>
            <div>
              <span className="text-sm font-medium">LinkedIn: </span>
              {user.linkedin_url ? (
                <a
                  href={user.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                >
                  <Linkedin className="size-4" />
                  {user.linkedin_url}
                </a>
              ) : (
                <span className="text-sm text-muted-foreground">
                  Not provided
                </span>
              )}
            </div>
            <div>
              <span className="text-sm font-medium">GitHub: </span>
              {user.github_url ? (
                <a
                  href={user.github_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-sm text-primary hover:underline inline-flex items-center gap-1"
                >
                  <Github className="size-4" />
                  {user.github_url}
                </a>
              ) : (
                <span className="text-sm text-muted-foreground">
                  Not provided
                </span>
              )}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Experiences Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold tracking-tight">
            Work Experience
          </h2>
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
        {isLoadingExperiences ? (
          <div className="text-center text-muted-foreground">
            Loading experiences...
          </div>
        ) : experiences && experiences.length > 0 ? (
          <div className="space-y-4">
            {experiences.map((experience) => (
              <ExperienceCard
                key={experience.id}
                experience={experience}
                userId={user.id}
              />
            ))}
          </div>
        ) : (
          <div className="text-center text-muted-foreground">
            No experiences yet. Click &quot;Add Experience&quot; to get started.
          </div>
        )}
      </div>

      {/* Education Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold tracking-tight">Education</h2>
          <Button
            onClick={() => {
              setShowAddEducationDialog(true);
            }}
          >
            <Plus className="mr-2 size-4" />
            Add Education
          </Button>
        </div>
        {isLoadingEducation ? (
          <div className="text-center text-muted-foreground">
            Loading education...
          </div>
        ) : education && education.length > 0 ? (
          <div className="space-y-4">
            {education.map((edu) => (
              <EducationCard key={edu.id} education={edu} userId={user.id} />
            ))}
          </div>
        ) : (
          <div className="text-center text-muted-foreground">
            No education entries yet. Click &quot;Add Education&quot; to get
            started.
          </div>
        )}
      </div>

      {/* Certificates Section */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-semibold tracking-tight">
            Certificates
          </h2>
          <Button
            onClick={() => {
              setShowAddCertificateDialog(true);
            }}
          >
            <Plus className="mr-2 size-4" />
            Add Certificate
          </Button>
        </div>
        {isLoadingCertificates ? (
          <div className="text-center text-muted-foreground">
            Loading certificates...
          </div>
        ) : certificates && certificates.length > 0 ? (
          <div className="space-y-4">
            {certificates.map((cert) => (
              <CertificateCard
                key={cert.id}
                certificate={cert}
                userId={user.id}
              />
            ))}
          </div>
        ) : (
          <div className="text-center text-muted-foreground">
            No certificates yet. Click &quot;Add Certificate&quot; to get
            started.
          </div>
        )}
      </div>

      {/* Edit Profile Dialog */}
      <Dialog
        open={showEditProfileDialog}
        onOpenChange={setShowEditProfileDialog}
      >
        <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Edit Profile</DialogTitle>
            <DialogDescription>
              Update your profile information.
            </DialogDescription>
          </DialogHeader>
          <Form {...userProfileForm}>
            <form
              onSubmit={userProfileForm.handleSubmit(onUpdateProfile)}
              className="space-y-4"
            >
              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={userProfileForm.control}
                  name="first_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>First Name *</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={userProfileForm.control}
                  name="last_name"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Last Name *</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={userProfileForm.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={userProfileForm.control}
                name="phone_number"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phone Number</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <div className="grid grid-cols-2 gap-4">
                <FormField
                  control={userProfileForm.control}
                  name="city"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>City</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
                <FormField
                  control={userProfileForm.control}
                  name="state"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>State</FormLabel>
                      <FormControl>
                        <Input {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </div>

              <FormField
                control={userProfileForm.control}
                name="linkedin_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>LinkedIn URL</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="https://linkedin.com/in/yourprofile"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={userProfileForm.control}
                name="github_url"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>GitHub URL</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="https://github.com/yourusername"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <DialogFooter>
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setShowEditProfileDialog(false);
                    userProfileForm.reset();
                  }}
                >
                  Cancel
                </Button>
                <Button type="submit" disabled={updateUser.isPending}>
                  {updateUser.isPending ? "Saving..." : "Save"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Add Experience Dialog */}
      <Dialog
        open={showAddExperienceDialog}
        onOpenChange={setShowAddExperienceDialog}
      >
        <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
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
                      <FormDescription>
                        Leave empty for current position
                      </FormDescription>
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
                      <Input
                        {...field}
                        placeholder="e.g., Python, SQL, Project Management"
                      />
                    </FormControl>
                    <FormDescription>
                      Separate skills with commas
                    </FormDescription>
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
