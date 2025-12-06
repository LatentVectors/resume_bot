"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";

import { certificatesAPI } from "@/lib/api/certificates";
import type { CertificationInsert, CertificationUpdate } from "@resume/database/types";

/**
 * Hook to create a new certificate.
 */
export function useCreateCertificate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { user_id: number; data: Omit<CertificationInsert, "user_id"> }) =>
      certificatesAPI.create(params),
    onSuccess: (_, variables) => {
      // Invalidate certificates list queries
      queryClient.invalidateQueries({ queryKey: ["certificates", variables.user_id] });
    },
  });
}

/**
 * Hook to update a certificate.
 */
export function useUpdateCertificate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (params: { certificateId: number; data: CertificationUpdate }) =>
      certificatesAPI.update(params.certificateId, params.data),
    onSuccess: (data) => {
      // Invalidate specific certificate and certificates list
      queryClient.invalidateQueries({ queryKey: ["certificates", data.id] });
      queryClient.invalidateQueries({ queryKey: ["certificates", data.user_id] });
    },
  });
}

/**
 * Hook to delete a certificate.
 */
export function useDeleteCertificate() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (certificateId: number) => certificatesAPI.delete(certificateId),
    onSuccess: () => {
      // Invalidate all certificates queries
      queryClient.invalidateQueries({ queryKey: ["certificates"] });
    },
  });
}

