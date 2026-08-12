"""Document Ingestion Pipeline (DIP).

Standalone tooling, not a Downstream service and not a connector — see
docs/architecture/DSH_Ingestion_Pipeline_Architecture.md. Scope for this
package, per the approved implementation plan: Phase A (manifest), Phase B
(OCR benchmark), Phase D (deterministic synthetic revision diff) only.
Phase C (real structured extraction) and Phase E (RES promotion) are not
implemented here.
"""
