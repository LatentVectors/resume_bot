"use client";

import { useState, useEffect } from "react";
import { Edit, Trash2 } from "lucide-react";
import { DeleteConfirmationDialog } from "@/components/ui/delete-confirmation-dialog";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
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
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import * as z from "zod";
import {
  useCreateEducation,
  useUpdateEducation,
  useDeleteEducation,
} from "@/lib/hooks/useEducationMutations";
import type { Education } from "@resume/database/types";

const educationSchema = z.object({
  institution: z.string().min(1, "Institution is required"),
  degree: z.string().min(1, "Degree is required"),
  major: z.string().min(1, "Major is required"),
  grad_date: z.string().min(1, "Graduation date is required"),
});

type EducationFormData = z.infer<typeof educationSchema>;

interface EducationCardProps {
  education: Education | null;
  userId: number;
  onAdd?: () => void;
}

export function EducationCard({
  education,
  userId,
  onAdd,
}: EducationCardProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const createEducation = useCreateEducation();
  const updateEducation = useUpdateEducation();
  const deleteEducation = useDeleteEducation();

  const isEditing = !!education;

  const form = useForm<EducationFormData>({
    resolver: zodResolver(educationSchema),
    defaultValues: {
      institution: education?.institution || "",
      degree: education?.degree || "",
      major: education?.major || "",
      grad_date: education?.grad_date || "",
    },
  });

  const onSubmit = async (data: EducationFormData) => {
    try {
      if (isEditing && education) {
        await updateEducation.mutateAsync({
          educationId: education.id,
          data,
        });
      } else {
        await createEducation.mutateAsync({
          user_id: userId,
          data,
        });
      }
      setShowDialog(false);
      form.reset();
      onAdd?.();
    } catch (error) {
      console.error("Failed to save education:", error);
    }
  };

  const onDelete = async () => {
    if (!education) return;
    try {
      await deleteEducation.mutateAsync(education.id);
      setShowDeleteDialog(false);
    } catch (error) {
      console.error("Failed to delete education:", error);
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "long",
    });
  };

  // Auto-open dialog when component mounts in add mode
  useEffect(() => {
    if (!education && onAdd && !showDialog) {
      // Use setTimeout to avoid synchronous setState in effect
      const timeoutId = setTimeout(() => {
        setShowDialog(true);
      }, 0);
      return () => clearTimeout(timeoutId);
    }
  }, [education, onAdd, showDialog]);

  // If no education and no onAdd callback, don't render anything
  if (!education && !onAdd) {
    return null;
  }

  // If onAdd is provided but no education, render only the dialog (for add mode)
  if (!education && onAdd) {
    return (
      <Dialog open={showDialog} onOpenChange={(open) => {
        setShowDialog(open);
        if (!open) {
          onAdd();
        }
      }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Education</DialogTitle>
            <DialogDescription>Add a new education entry.</DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="institution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Institution *</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="degree"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Degree *</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="e.g., Bachelor of Science" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="major"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Major *</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="e.g., Computer Science" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="grad_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Graduation Date *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
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
                    setShowDialog(false);
                    form.reset();
                    onAdd();
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createEducation.isPending || updateEducation.isPending}
                >
                  {createEducation.isPending || updateEducation.isPending
                    ? "Saving..."
                    : "Add"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <>
      <Card>
        <CardHeader>
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <CardTitle>{education?.degree || "Add Education"}</CardTitle>
              <CardDescription>
                {education
                  ? `${education.institution} - ${education.major}`
                  : "Click edit to add your education"}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {education && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      form.reset({
                        institution: education.institution,
                        degree: education.degree,
                        major: education.major,
                        grad_date: education.grad_date,
                      });
                      setShowDialog(true);
                    }}
                  >
                    <Edit className="size-4" />
                  </Button>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-destructive hover:text-destructive"
                    onClick={() => setShowDeleteDialog(true)}
                  >
                    <Trash2 className="size-4" />
                  </Button>
                </>
              )}
            </div>
          </div>
        </CardHeader>
        {education && (
          <CardContent>
            <div className="text-sm text-muted-foreground">
              Graduated: {formatDate(education.grad_date)}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isEditing ? "Edit Education" : "Add Education"}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update your education details."
                : "Add a new education entry."}
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="institution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Institution *</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="degree"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Degree *</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="e.g., Bachelor of Science" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="major"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Major *</FormLabel>
                    <FormControl>
                      <Input {...field} placeholder="e.g., Computer Science" />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="grad_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Graduation Date *</FormLabel>
                    <FormControl>
                      <Input type="date" {...field} />
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
                    setShowDialog(false);
                    form.reset();
                  }}
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  disabled={createEducation.isPending || updateEducation.isPending}
                >
                  {createEducation.isPending || updateEducation.isPending
                    ? "Saving..."
                    : isEditing
                      ? "Update"
                      : "Add"}
                </Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>

      {/* Delete Dialog */}
      {education && (
        <DeleteConfirmationDialog
          open={showDeleteDialog}
          onOpenChange={setShowDeleteDialog}
          onConfirm={onDelete}
          itemName={`${education.degree} from ${education.institution}`}
          itemType="Education"
          isDeleting={deleteEducation.isPending}
        />
      )}
    </>
  );
}

