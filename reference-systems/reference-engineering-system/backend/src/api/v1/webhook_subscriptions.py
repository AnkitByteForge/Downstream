from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import (
    get_list_webhook_subscriptions,
    get_register_webhook_subscription,
)
from api.schemas.webhook import WebhookSubscriptionIn, WebhookSubscriptionOut
from application.use_cases.webhook_use_cases import (
    ListWebhookSubscriptions,
    RegisterWebhookSubscription,
)

router = APIRouter(prefix="/webhook_subscriptions", tags=["webhook_subscriptions"])


def _out(subscription) -> WebhookSubscriptionOut:
    return WebhookSubscriptionOut(
        id=subscription.id,
        project_id=subscription.project_id,
        resource_name=subscription.resource_name,
        event_type=subscription.event_type,
        target_url=subscription.target_url,
    )


@router.post("", response_model=WebhookSubscriptionOut)
def register_webhook_subscription(
    project_id: int,
    body: WebhookSubscriptionIn,
    use_case: RegisterWebhookSubscription = Depends(get_register_webhook_subscription),
) -> WebhookSubscriptionOut:
    subscription = use_case.execute(
        project_id, body.resource_name, body.event_type, body.target_url, body.secret
    )
    return _out(subscription)


@router.get("", response_model=list[WebhookSubscriptionOut])
def list_webhook_subscriptions(
    project_id: int,
    use_case: ListWebhookSubscriptions = Depends(get_list_webhook_subscriptions),
) -> list[WebhookSubscriptionOut]:
    return [_out(s) for s in use_case.execute(project_id)]
