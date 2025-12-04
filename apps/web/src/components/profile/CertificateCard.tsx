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
  useCreateCertificate,
  useUpdateCertificate,
  useDeleteCertificate,
} from "@/lib/hooks/useCertificateMutations";
import type { Certification } from "@resume/database/types";

const certificateSchema = z.object({
  title: z.string().min(1, "Title is required"),
  institution: z.string().optional(),
  date: z.string().min(1, "Date is required"),
});

type CertificateFormData = z.infer<typeof certificateSchema>;

interface CertificateCardProps {
  certificate: Certification | null;
  userId: number;
  onAdd?: () => void;
}

export function CertificateCard({
  certificate,
  userId,
  onAdd,
}: CertificateCardProps) {
  const [showDialog, setShowDialog] = useState(false);
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);

  const createCertificate = useCreateCertificate();
  const updateCertificate = useUpdateCertificate();
  const deleteCertificate = useDeleteCertificate();

  const isEditing = !!certificate;

  const form = useForm<CertificateFormData>({
    resolver: zodResolver(certificateSchema),
    defaultValues: {
      title: certificate?.title || "",
      institution: certificate?.institution || "",
      date: certificate?.date || "",
    },
  });

  const onSubmit = async (data: CertificateFormData) => {
    try {
      if (isEditing && certificate) {
        await updateCertificate.mutateAsync({
          certificateId: certificate.id,
          data: {
            title: data.title,
            institution: data.institution || null,
            date: data.date,
          },
        });
      } else {
        await createCertificate.mutateAsync({
          user_id: userId,
          data: {
            title: data.title,
            institution: data.institution || null,
            date: data.date,
          },
        });
      }
      setShowDialog(false);
      form.reset();
      onAdd?.();
    } catch (error) {
      console.error("Failed to save certificate:", error);
    }
  };

  const onDelete = async () => {
    if (!certificate) return;
    try {
      await deleteCertificate.mutateAsync(certificate.id);
      setShowDeleteDialog(false);
    } catch (error) {
      console.error("Failed to delete certificate:", error);
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
    if (!certificate && onAdd && !showDialog) {
      // Use setTimeout to avoid synchronous setState in effect
      const timeoutId = setTimeout(() => {
        setShowDialog(true);
      }, 0);
      return () => clearTimeout(timeoutId);
    }
  }, [certificate, onAdd, showDialog]);

  // If no certificate and no onAdd callback, don't render anything
  if (!certificate && !onAdd) {
    return null;
  }

  // If onAdd is provided but no certificate, render only the dialog (for add mode)
  if (!certificate && onAdd) {
    return (
      <Dialog
        open={showDialog}
        onOpenChange={(open) => {
          setShowDialog(open);
          if (!open) {
            onAdd();
          }
        }}
      >
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Add Certificate</DialogTitle>
            <DialogDescription>Add a new certificate.</DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Title *</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="e.g., AWS Certified Solutions Architect"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="institution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Institution</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="e.g., Amazon Web Services"
                      />
                    </FormControl>
                    <FormDescription>Issuing organization</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date *</FormLabel>
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
                  disabled={
                    createCertificate.isPending || updateCertificate.isPending
                  }
                >
                  {createCertificate.isPending || updateCertificate.isPending
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
              <CardTitle>{certificate?.title || "Add Certificate"}</CardTitle>
              <CardDescription>
                {certificate
                  ? certificate.institution
                    ? `${certificate.institution} - ${formatDate(
                        certificate.date
                      )}`
                    : formatDate(certificate.date)
                  : "Click edit to add a certificate"}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {certificate && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      form.reset({
                        title: certificate.title,
                        institution: certificate.institution || "",
                        date: certificate.date,
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
        {certificate && (
          <CardContent>
            <div className="text-sm text-muted-foreground">
              Issued: {formatDate(certificate.date)}
            </div>
          </CardContent>
        )}
      </Card>

      {/* Add/Edit Dialog */}
      <Dialog open={showDialog} onOpenChange={setShowDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {isEditing ? "Edit Certificate" : "Add Certificate"}
            </DialogTitle>
            <DialogDescription>
              {isEditing
                ? "Update certificate details."
                : "Add a new certificate."}
            </DialogDescription>
          </DialogHeader>
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="title"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Title *</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="e.g., AWS Certified Solutions Architect"
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="institution"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Institution</FormLabel>
                    <FormControl>
                      <Input
                        {...field}
                        placeholder="e.g., Amazon Web Services"
                      />
                    </FormControl>
                    <FormDescription>Issuing organization</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              <FormField
                control={form.control}
                name="date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Date *</FormLabel>
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
                  disabled={
                    createCertificate.isPending || updateCertificate.isPending
                  }
                >
                  {createCertificate.isPending || updateCertificate.isPending
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
      {certificate && (
        <DeleteConfirmationDialog
          open={showDeleteDialog}
          onOpenChange={setShowDeleteDialog}
          onConfirm={onDelete}
          itemName={certificate.title}
          itemType="Certificate"
          isDeleting={deleteCertificate.isPending}
        />
      )}
    </>
  );
}
