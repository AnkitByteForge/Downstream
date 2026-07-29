"""The shared adapter contract every Connector implements
(fetchEngineeringEvents, fetchArtifactSnapshot, pushAction, healthCheck),
per packages/connector-interface's scope in
docs/07_Downstream_Implementation_Blueprint.md §2 and §7.
"""

from connector_interface.interface import ConnectorInterface
from connector_interface.types import (
    ActionPayload,
    ConnectionHealth,
    DispatchReceipt,
    DispatchStatus,
)

__all__ = [
    "ActionPayload",
    "ConnectionHealth",
    "ConnectorInterface",
    "DispatchReceipt",
    "DispatchStatus",
]
