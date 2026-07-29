"""The Connector Interface — the contract every adapter implements,
regardless of source system (docs/03_Downstream_Systems_Architecture.md §1;
signatures restated verbatim in docs/07_Downstream_Implementation_Blueprint.md
§7):

    fetchEngineeringEvents(since: cursor)  -> EngineeringEventEnvelope[]
    fetchArtifactSnapshot(artifactRef)     -> CommercialArtifactSnapshot
    pushAction(action: ActionPayload)      -> DispatchReceipt
    healthCheck()                          -> ConnectionHealth

Method names below are translated to snake_case, and `cursor`/`artifactRef`
are typed as `str` — an opaque pagination/watermark token and an artifact
reference respectively, since no other shape is specified anywhere in the
frozen docs. Both are pure Python-naming-convention translations with zero
effect on the contract itself, per docs/07's own stated allowance for such
translations ("a pure implementation detail with zero effect on the
architecture").

This is deliberately ONE interface, not split by connector family
(Engineering vs. Commercial): docs/03 §1 states it applies "regardless of
source system," and docs/04's Procore analysis confirms a single connection
may need to serve both envelope families at once. An adapter that only ever
supports one family (e.g. Connector-SAP, which is "unambiguously
Commercial-only" per docs/04) is still expected to implement the full
interface — it simply raises NotImplementedError (or returns an empty
result, at the implementing service's discretion; that decision belongs to
the service, not this shared contract) for the methods that don't apply to
it. Nothing here builds that service-level behavior — implementing services
are explicitly out of scope for Milestone 0.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from envelope_schemas import CommercialArtifactSnapshot, EngineeringEventEnvelope

from connector_interface.types import ActionPayload, ConnectionHealth, DispatchReceipt


class ConnectorInterface(ABC):
    """Abstract base class every Connector adapter (wired or stub) must
    subclass and fully implement."""

    @abstractmethod
    def fetch_engineering_events(self, since: str) -> list[EngineeringEventEnvelope]:
        """Pull (or drain a webhook-fed queue of) engineering events that
        occurred since `since`, a source-agnostic opaque cursor. Pull or
        webhook-push is the adapter's own internal choice; this output
        contract is identical either way (docs/03 §1)."""
        raise NotImplementedError

    @abstractmethod
    def fetch_artifact_snapshot(self, artifact_ref: str) -> CommercialArtifactSnapshot:
        """On demand, get the current state (status, value, lifecycle
        position) of one Commercial Artifact."""
        raise NotImplementedError

    @abstractmethod
    def push_action(self, action: ActionPayload) -> DispatchReceipt:
        """Send a drafted communication or a write-back transaction. Always
        returns a receipt; never assumes success (docs/03 §1)."""
        raise NotImplementedError

    @abstractmethod
    def health_check(self) -> ConnectionHealth:
        """Report the scope granted, last successful sync, and error state
        of this connection."""
        raise NotImplementedError
