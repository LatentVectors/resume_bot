/**
 * Certifications API client endpoints.
 */

import { apiRequest } from "./client";
import type { Certification, CertificationInsert, CertificationUpdate } from "@resume/database/types";

export const certificatesAPI = {
  /**
   * List all certifications for a user.
   */
  list: (userId: number): Promise<Certification[]> => {
    const queryParams = new URLSearchParams({
      user_id: userId.toString(),
    });
    return apiRequest<Certification[]>(`/api/certifications?${queryParams.toString()}`);
  },

  /**
   * Get a specific certification.
   */
  get: (certificationId: number): Promise<Certification> => {
    return apiRequest<Certification>(`/api/certifications/${certificationId}`);
  },

  /**
   * Create a new certification.
   */
  create: (params: { user_id: number; data: Omit<CertificationInsert, "user_id"> }): Promise<Certification> => {
    const queryParams = new URLSearchParams({
      user_id: params.user_id.toString(),
    });
    return apiRequest<Certification>(`/api/certifications?${queryParams.toString()}`, {
      method: "POST",
      body: JSON.stringify(params.data),
    });
  },

  /**
   * Update a certification.
   */
  update: (certificationId: number, data: CertificationUpdate): Promise<Certification> => {
    return apiRequest<Certification>(`/api/certifications/${certificationId}`, {
      method: "PATCH",
      body: JSON.stringify(data),
    });
  },

  /**
   * Delete a certification.
   */
  delete: (certificationId: number): Promise<void> => {
    return apiRequest<void>(`/api/certifications/${certificationId}`, {
      method: "DELETE",
    });
  },
};
