import { apiClient } from "./client";
import type {
  ActivityEntryOut,
  DesignChangeOut,
  DrawingOut,
  DrawingVersionOut,
  LocationOut,
  ModelObjectOut,
  ProjectOut,
  RFIOut,
  ScheduleActivityOut,
  SessionOut,
  SpecDivisionOut,
  SpecSectionOut,
  SubmittalOut,
  SubmittalRequirementOut,
  SubmittalRevisionOut,
  VendorOut,
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

export const specDivisionsApi = {
  list: () => apiClient.get<SpecDivisionOut[]>("/rest/v1.0/spec_divisions"),
};

export const vendorsApi = {
  list: (projectId: number) => apiClient.get<VendorOut[]>(`/rest/v1.0/projects/${projectId}/vendors`),
};

export const submittalRequirementsApi = {
  list: (projectId: number, specSectionId?: number) =>
    apiClient.get<SubmittalRequirementOut[]>(
      `/rest/v1.0/projects/${projectId}/submittal_requirements${
        specSectionId != null ? `?spec_section_id=${specSectionId}` : ""
      }`
    ),
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

export const designChangesApi = {
  list: (projectId: number) =>
    apiClient.get<DesignChangeOut[]>(`/rest/v1.0/projects/${projectId}/design_changes`),
  get: (projectId: number, changeId: number) =>
    apiClient.get<DesignChangeOut>(
      `/rest/v1.0/projects/${projectId}/design_changes/${changeId}`
    ),
  issue: (projectId: number, changeId: number) =>
    apiClient.patch<DesignChangeOut>(
      `/rest/v1.0/projects/${projectId}/design_changes/${changeId}/issue`
    ),
  acknowledge: (projectId: number, changeId: number) =>
    apiClient.patch<DesignChangeOut>(
      `/rest/v1.0/projects/${projectId}/design_changes/${changeId}/acknowledge`
    ),
  voidChange: (projectId: number, changeId: number) =>
    apiClient.patch<DesignChangeOut>(
      `/rest/v1.0/projects/${projectId}/design_changes/${changeId}/void`
    ),
};

export const scheduleActivitiesApi = {
  list: (projectId: number) =>
    apiClient.get<ScheduleActivityOut[]>(`/rest/v1.0/projects/${projectId}/schedule_activities`),
  get: (projectId: number, scheduleActivityId: number) =>
    apiClient.get<ScheduleActivityOut>(
      `/rest/v1.0/projects/${projectId}/schedule_activities/${scheduleActivityId}`
    ),
};

export const modelObjectsApi = {
  list: (projectId: number) =>
    apiClient.get<ModelObjectOut[]>(`/rest/v1.0/projects/${projectId}/model_objects`),
  get: (projectId: number, modelObjectId: number) =>
    apiClient.get<ModelObjectOut>(
      `/rest/v1.0/projects/${projectId}/model_objects/${modelObjectId}`
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

export const activityApi = {
  list: (projectId: number) =>
    apiClient.get<ActivityEntryOut[]>(`/rest/v1.0/projects/${projectId}/activity`),
};

export const submittalsApi = {
  list: (projectId: number) =>
    apiClient.get<SubmittalOut[]>(`/rest/v1.0/projects/${projectId}/submittals`),
  get: (projectId: number, submittalId: number) =>
    apiClient.get<SubmittalOut>(`/rest/v1.0/projects/${projectId}/submittals/${submittalId}`),
  revisions: (projectId: number, submittalId: number) =>
    apiClient.get<SubmittalRevisionOut[]>(
      `/rest/v1.0/projects/${projectId}/submittals/${submittalId}/revisions`
    ),
  recordDisposition: (
    projectId: number,
    submittalId: number,
    revisionId: number,
    reviewStatusCode: string,
    disposedByUserId: number
  ) =>
    apiClient.patch<SubmittalRevisionOut>(
      `/rest/v1.0/projects/${projectId}/submittals/${submittalId}/revisions/${revisionId}/disposition`,
      { review_status_code: reviewStatusCode, disposed_by_user_id: disposedByUserId }
    ),
};
