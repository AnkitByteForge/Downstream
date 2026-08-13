-- Milestone 0 seed row, updated for Milestone 2 (approved remedy (a)):
-- connector-procore's connection to the Reference Engineering System now
-- uses RES's seeded FULL-scope OAuth client (meridian_tower.py:
-- client_id="downstream-full", client_secret="full-scope-secret",
-- integration_user_id=full_scope_integration -> PermissionScope.full()).
--
-- Why changed from Milestone 1's downstream-partial: verified live during
-- M1 that the partial-scope credential (scope=["rfis","submittals",
-- "documents"]) cannot see spec_sections at all, so the real Trigger's
-- spec_section_refs was always []  — Key Resolution (Milestone 2) has
-- nothing to resolve against without it. This is a one-row config change,
-- not a new grant type and not a connector redesign: connector-procore's
-- own OAuth client_credentials logic and its
-- _acting_credential_scope_wire_value() mapper already handle a "*"
-- granted_scope correctly (implemented in Milestone 1, unmodified here) —
-- it already emits acting_credential_scope="full" when granted_scope
-- contains RES's own PermissionScope.FULL_SCOPE_MARKER ("*"), the same
-- sentinel RES itself uses internally.
--
-- source_system is recorded as 'procore' (not 'reference-engineering-system')
-- because the EngineeringEventEnvelope.source_system convention documented
-- across docs/03-07 names the *role* a connector plays ('procore', 'acc'),
-- and RES is explicitly built to play that role (docs/engineering/
-- RES_IMPLEMENTATION_CONTEXT.md: "a vendor-neutral Procore/ACC-realistic
-- external engineering system"). base_url/oauth_token_url point at the real
-- running reference-engineering-backend container, per the approved decision
-- to use RES directly as Milestone 1's integration target rather than a
-- separate mock.
--
-- webhook_secret matches meridian_tower.py's DEFAULT_WEBHOOK_SECRET
-- constant ("seed-webhook-secret") — a dev-only credential already
-- committed in cleartext in RES's own seed script; reusing the same known
-- value here rather than inventing a second one to manage.
--
-- ON CONFLICT ... DO UPDATE (not DO NOTHING, as in Milestone 1): this row
-- must actually change on re-run against an environment that was already
-- seeded under Milestone 1's downstream-partial row, not just be skipped.

INSERT INTO connector_configurations (
    connection_id, project_id, source_system, base_url, oauth_token_url,
    oauth_client_id, oauth_client_secret, granted_scope, integration_tier,
    webhook_secret
) VALUES (
    'conn_res_meridian',
    'proj_meridian_tower',
    'procore',
    'http://reference-engineering-backend:8000',
    'http://reference-engineering-backend:8000/oauth/token',
    'downstream-full',
    'full-scope-secret',
    '["*"]',
    'read_only',
    'seed-webhook-secret'
)
ON CONFLICT (connection_id) DO UPDATE SET
    oauth_client_id = EXCLUDED.oauth_client_id,
    oauth_client_secret = EXCLUDED.oauth_client_secret,
    granted_scope = EXCLUDED.granted_scope;
