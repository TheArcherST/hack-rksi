import logging
from email.message import EmailMessage
from typing import Annotated

import aiosmtplib
from dishka import FromDishka
from dishka.integrations.taskiq import inject
from taskiq import Context, TaskiqDepends

from hack.core.providers import ConfigEmail
from hack.tasks.brokers.default import default_broker

logger = logging.getLogger(__name__)


@default_broker.task()
@inject(patch_module=True)
async def send_email(
        context: Annotated[Context, TaskiqDepends()],
        email_config: FromDishka[ConfigEmail],
        to_email: str,
        subject: str,
        content: str,
        html_content: str | None = None,
) -> None:
    message = EmailMessage()
    message["To"] = to_email
    message["Subject"] = subject
    message["From"] = email_config.from_email

    message.set_content(content)
    if html_content:
        message.add_alternative(html_content, subtype="html")

    task_id = context.message.task_id
    if email_config.backend == "console":
        logger.info(
            "Email queued (console backend); to=%s subject=%s task_id=%s",
            to_email,
            subject,
            task_id,
        )
        return

    await aiosmtplib.send(
        message,
        hostname=email_config.host,
        port=email_config.port,
        username=email_config.username,
        password=email_config.password,
        start_tls=email_config.start_tls,
        use_tls=email_config.use_tls,
        timeout=email_config.timeout,
    )
