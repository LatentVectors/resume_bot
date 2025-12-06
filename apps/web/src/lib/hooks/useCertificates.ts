"use client";

import { useQuery } from "@tanstack/react-query";

import { certificatesAPI } from "@/lib/api/certificates";

/**
 * Hook to fetch list of certificates for a user.
 */
export function useCertificates(userId: number) {
  return useQuery({
    queryKey: ["certificates", userId],
    queryFn: () => certificatesAPI.list(userId),
    enabled: !!userId,
  });
}

