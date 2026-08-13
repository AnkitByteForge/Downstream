-- Milestone 0 seed row — the one connector configuration Milestone 1 needs:
-- connector-procore's connection to the Reference Engineering System, using
-- RES's own seeded partial-scope OAuth client (meridian_tower.py:
-- client_id="downstream-partial", client_secret="partial-scope-secret",
-- scope=["rfis","submittals","documents"]). Deliberately the partial-scope
-- client, not the full-scope one — this exercises the
-- acting_credential_scope="partial:[...]" path docs/04/05 identify as the
-- single highest-value real-world behavior to get right, for free, since RES
-- already has it seeded.
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
    'downstream-partial',
    'partial-scope-secret',
    '["rfis","submittals","documents"]',
    'read_only',
    'seed-webhook-secret'
)
ON CONFLICT (connection_id) DO NOTHING;
