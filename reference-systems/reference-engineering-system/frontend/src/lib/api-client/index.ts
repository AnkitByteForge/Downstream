import { apiClient } from "./client";
import type {
  DrawingOut,
  DrawingVersionOut,
  LocationOut,
  ProjectOut,
  RFIOut,
  SessionOut,
  SpecSectionOut,
} from "./types";

export * from "./types";
export { ApiError } from "./client";

export const authApi = {
  login: (email: string, password: string) =>
    apiClient.post<{ status: string }>("/auth/login", { email, password }),
  logout: () => apiClient.post<{ status: string }>("/auth/logout"),
  session: () => apiClient.get<SessionOut>("/auth/session"),
};

export const projectsApi = {
  list: () => apiClient.get<ProjectOut[]>("/rest/v1.0/projects"),
  get: (projectId: number) => apiClient.get<ProjectOut>(`/rest/v1.0/projects/${projectId}`),
};

export const locationsApi = {
  list: (projectId: number) =>
    apiClient.get<LocationOut[]>(`/rest/v1.0/projects/${projectId}/locations`),
};

export const specSectionsApi = {
  list: (projectId: number) =>
    apiClient.get<SpecSectionOut[]>(`/rest/v1.0/projects/${projectId}/spec_sections`),
};

export const documentsApi = {
  list: (projectId: number) =>
    apiClient.get<DrawingOut[]>(`/rest/v1.0/projects/${projectId}/documents`),
  get: (projectId: number, drawingId: number) =>
    apiClient.get<DrawingOut>(`/rest/v1.0/projects/${projectId}/documents/${drawingId}`),
  versions: (projectId: number, drawingId: number) =>
    apiClient.get<DrawingVersionOut[]>(
      `/rest/v1.0/projects/${projectId}/documents/${drawingId}/versions`
    ),
  getVersion: (projectId: number, versionId: number) =>
    apiClient.get<DrawingVersionOut>(
      `/rest/v1.0/projects/${projectId}/documents/versions/${versionId}`
    ),
};

export const rfisApi = {
  list: (projectId: number) => apiClient.get<RFIOut[]>(`/rest/v1.0/projects/${projectId}/rfis`),
  get: (projectId: number, rfiId: number) =>
    apiClient.get<RFIOut>(`/rest/v1.0/projects/${projectId}/rfis/${rfiId}`),
  respond: (projectId: number, rfiId: number, responseText: string, managerUserId: number) =>
    apiClient.patch<RFIOut>(`/rest/v1.0/projects/${projectId}/rfis/${rfiId}/respond`, {
      response_text: responseText,
      manager_user_id: managerUserId,
    }),
  close: (projectId: number, rfiId: number, responseText?: string) =>
    apiClient.patch<RFIOut>(`/rest/v1.0/projects/${projectId}/rfis/${rfiId}/close`, {
      response_text: responseText,
    }),
};
