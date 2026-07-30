# mock-erp

Mock SAP/Oracle — models the shared shape of the commercial systems of
record, per `04_Downstream_Connector_Layer_Validation.md`. Its job is to
exercise the CSRF-token ceremony, thin business-event webhooks requiring an
enrichment call-back, org-scoping fields (company code/plant), and
idempotent write-back.

No mock behavior has been implemented yet. This folder is scaffold only.
