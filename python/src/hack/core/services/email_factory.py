from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from jinja2 import Environment, FileSystemLoader, select_autoescape

from hack.core.models.notification_events import (
    AdminSetPasswordNotification,
    EventCreatedNotification,
    EventParticipationCancelledNotification,
    EventParticipationConfirmedNotification,
    EventReminderNotification,
    EventUpdatedNotification,
    NotificationEvent,
    NotificationEventTypeEnum,
    PasswordChangedEvent,
    PasswordResetLinkEvent,
    RegistrationConfirmCodeEvent,
    RegistrationWelcomeEvent,
    RenderedEmail,
)
from hack.core.providers import ConfigTemplates

BRAND_NAME = "TTK Афиша"
FOOTER_NOTE = (
    "Это письмо отправлено автоматически сервисом «Афиша TTK». "
    "Вы получили его, потому что участвуете в корпоративных мероприятиях."
)


class EmailFactory:
    def __init__(
            self,
            config_templates: ConfigTemplates,
            template_dirs: Iterable[Path] | None = None,
            brand_name: str = BRAND_NAME,
    ):
        self._config_templates = config_templates
        paths = list(template_dirs or self._default_template_dirs())
        if not paths:
            raise FileNotFoundError("Email templates directory was not found")

        self._env = Environment(
            loader=FileSystemLoader(paths),
            autoescape=select_autoescape(["html"]),
        )
        self._brand_name = brand_name

    def build(self, event: NotificationEvent) -> RenderedEmail:
        match event.type:
            case NotificationEventTypeEnum.REG_CONFIRM_CODE:
                return self._render_registration_confirm(event)
            case NotificationEventTypeEnum.REG_WELCOME:
                return self._render_registration_welcome(event)
            case NotificationEventTypeEnum.PASSWORD_RESET_LINK:
                return self._render_password_reset(event)
            case NotificationEventTypeEnum.PASSWORD_CHANGED:
                return self._render_password_changed(event)
            case NotificationEventTypeEnum.EVENT_CREATED:
                return self._render_event_created(event)
            case NotificationEventTypeEnum.EVENT_UPDATED:
                return self._render_event_updated(event)
            case NotificationEventTypeEnum.EVENT_REMINDER:
                return self._render_event_reminder(event)
            case NotificationEventTypeEnum.EVENT_PARTICIPATION_CONFIRMED:
                return self._render_participation_confirmed(event)
            case NotificationEventTypeEnum.EVENT_PARTICIPATION_CANCELLED:
                return self._render_participation_cancelled(event)
            case NotificationEventTypeEnum.ADMIN_SET_PASSWORD:
                return self._render_admin_set_password(event)
        raise ValueError(f"Unsupported notification type: {event.type}")

    def _render_registration_confirm(
            self,
            event: RegistrationConfirmCodeEvent,
    ) -> RenderedEmail:
        subject = f"Код подтверждения {BRAND_NAME}: {event.verification_code}"
        text = (
            f"Здравствуйте, {event.full_name}!\n\n"
            f"Ваш код подтверждения: {event.verification_code}\n"
            "Введите его в приложении, чтобы завершить регистрацию."
        )
        ctx = {
            "title": subject,
            "greeting_name": event.full_name,
            "verification_code": event.verification_code,
            "lead": None,
        }
        return self._render("registration_confirm_code.html", subject, text, ctx)

    def _render_registration_welcome(
            self,
            event: RegistrationWelcomeEvent,
    ) -> RenderedEmail:
        subject = "Добро пожаловать в Афишу TTK"
        text = (
            f"Здравствуйте, {event.full_name}!\n\n"
            "Регистрация завершена. Мы будем присылать вам приглашения "
            "и напоминания о событиях, в которых вы участвуете."
        )
        ctx = {
            "title": subject,
            "greeting_name": event.full_name,
            "lead": None,
        }
        return self._render("registration_welcome.html", subject, text, ctx)

    def _render_password_reset(
            self,
            event: PasswordResetLinkEvent,
    ) -> RenderedEmail:
        subject = "Сброс пароля"
        date_text = self._format_expiration(event.expires_at)
        text = (
            "Мы получили запрос на сброс пароля.\n\n"
            f"Ссылка для восстановления: {event.reset_url}\n"
        )
        if date_text:
            text += f"Ссылка действует до {date_text}.\n"

        ctx = {
            "title": subject,
            "greeting_name": event.full_name,
            "lead": None,
            "cta_url": str(event.reset_url),
            "cta_label": "Сбросить пароль",
            "expires_at_text": date_text,
        }
        return self._render("password_reset_link.html", subject, text, ctx)

    def _render_password_changed(
            self,
            event: PasswordChangedEvent,
    ) -> RenderedEmail:
        subject = "Пароль изменен"
        greeting = event.full_name or "друг"
        text = (
            f"Здравствуйте, {greeting}!\n\n"
            "Пароль вашей учетной записи был изменен. "
            "Если это были не вы, срочно сбросьте пароль."
        )
        ctx = {
            "title": subject,
            "greeting_name": event.full_name,
            "lead": None,
        }
        return self._render("password_changed.html", subject, text, ctx)

    def _render_event_created(
            self,
            event: EventCreatedNotification,
    ) -> RenderedEmail:
        subject = f"Новое событие: {event.event_name}"
        text = self._event_text_lead(
            event,
            "Вы приглашены на новое событие.",
        )
        ctx = self._event_context(event, is_administrative_context=False)
        ctx.update({
            "title": subject,
            "lead": None,
            "cta_label": "Перейти к событию",
        })
        return self._render("event_created.html", subject, text, ctx)

    def _render_event_updated(
            self,
            event: EventUpdatedNotification,
    ) -> RenderedEmail:
        subject = f"Обновление события: {event.event_name}"
        summary = event.updates_summary or "Организатор внес изменения."
        text = self._event_text_lead(
            event,
            summary,
        )
        ctx = self._event_context(event, is_administrative_context=False)
        ctx.update({
            "title": subject,
            "lead": None,
            "cta_label": "Посмотреть изменения",
        })
        if event.updates_summary:
            ctx["updates_summary"] = event.updates_summary
        return self._render("event_updated.html", subject, text, ctx)

    def _render_event_reminder(
            self,
            event: EventReminderNotification,
    ) -> RenderedEmail:
        subject = f"Скоро начало: {event.event_name}"
        text = self._event_text_lead(
            event,
            f"Напоминание: событие начнется через {event.hours_before} часов.",
        )
        ctx = self._event_context(event, is_administrative_context=False)
        ctx.update({
            "title": subject,
            "lead": None,
            "cta_label": "Перейти к событию",
            "hours_before": event.hours_before,
        })
        return self._render("event_reminder.html", subject, text, ctx)

    def _render_participation_confirmed(
            self,
            event: EventParticipationConfirmedNotification,
    ) -> RenderedEmail:
        subject = (
            f"{event.participant_name} подтвердил участие: "
            f"{event.event_name}"
        )
        text = self._event_text_lead(
            event,
            f"{event.participant_name} присоединился к событию.",
        )
        ctx = self._event_context(event, is_administrative_context=True)
        ctx.update({
            "title": subject,
            "lead": None,
            "cta_label": "Открыть событие",
            "participant_name": event.participant_name,
        })
        return self._render(
            "event_participation_confirmed.html",
            subject,
            text,
            ctx,
        )

    def _render_participation_cancelled(
            self,
            event: EventParticipationCancelledNotification,
    ) -> RenderedEmail:
        subject = (
            f"{event.participant_name} отменил участие: "
            f"{event.event_name}"
        )
        text = self._event_text_lead(
            event,
            f"{event.participant_name} отменил участие в событии.",
        )
        ctx = self._event_context(event, is_administrative_context=True)
        ctx.update({
            "title": subject,
            "lead": None,
            "cta_label": "Открыть событие",
            "participant_name": event.participant_name,
        })
        return self._render(
            "event_participation_cancelled.html",
            subject,
            text,
            ctx,
        )

    def _render_admin_set_password(
            self,
            event: AdminSetPasswordNotification,
    ) -> RenderedEmail:
        subject = "Пароль обновлен администратором"
        greeting = event.full_name or "коллега"
        admin_name = event.admin_name or "администратор"
        text = (
            f"Здравствуйте, {greeting}!\n\n"
            f"{admin_name} установил для вас новый пароль.\n"
            f"Временный пароль: {event.temporary_password}\n"
            "Авторизуйтесь с ним и смените пароль в профиле."
        )
        ctx = {
            "title": subject,
            "greeting_name": event.full_name,
            "lead": None,
            "temporary_password": event.temporary_password,
        }
        return self._render("admin_set_password.html", subject, text, ctx)

    def _render(
            self,
            template_name: str,
            subject: str,
            text: str,
            context: dict[str, Any],
    ) -> RenderedEmail:
        ctx = {
            "brand_name": self._brand_name,
            "footer_note": FOOTER_NOTE,
            "subject": subject,
        }
        ctx.update(context)
        ctx.setdefault("title", subject)
        template = self._env.get_template(template_name)
        content = template.render(**ctx)
        return RenderedEmail(
            subject=subject,
            html_content=content,
            content=text.strip(),
            context=context,
        )

    def _event_context(
            self,
            event: (
                EventCreatedNotification
                | EventUpdatedNotification
                | EventReminderNotification
                | EventParticipationConfirmedNotification
                | EventParticipationCancelledNotification
            ),
            is_administrative_context: bool,
    ) -> dict[str, Any]:
        date_text, time_text = self._format_datetime(event.starts_at)
        cta_url = None
        if event.event_id is not None:
            template = (
                self._config_templates.event_url_template
                if is_administrative_context
                else self._config_templates.event_card_url_template
            )
            cta_url = template.format(event_id=event.event_id)
        return {
            "greeting_name": event.recipient_name,
            "event_name": event.event_name,
            "event_date": date_text,
            "event_time": time_text,
            "location": event.location,
            "participants_count": event.participants_count,
            "cta_url": cta_url,
        }

    def _format_datetime(self, value: datetime) -> tuple[str, str]:
        dt = value
        if dt.tzinfo is not None:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%d.%m.%Y"), dt.strftime("%H:%M")

    def _format_expiration(self, value: datetime | None) -> str | None:
        if value is None:
            return None
        date_text, time_text = self._format_datetime(value)
        return f"{date_text} {time_text} (UTC)"

    def _event_text_lead(
            self,
            event: (
                EventCreatedNotification
                | EventUpdatedNotification
                | EventReminderNotification
                | EventParticipationConfirmedNotification
                | EventParticipationCancelledNotification
            ),
            lead: str,
    ) -> str:
        date_text, time_text = self._format_datetime(event.starts_at)
        location = event.location or "Формат уточняется"
        return (
            f"{lead}\n\n"
            f"Событие: {event.event_name}\n"
            f"Когда: {date_text} в {time_text} (UTC)\n"
            f"Где: {location}"
        )

    def _default_template_dirs(self) -> list[Path]:
        base = Path(__file__).resolve()
        candidates: list[Path] = []
        for depth in (4, 5):
            try:
                candidate = base.parents[depth] / "templates" / "email"
            except IndexError:
                continue
            if candidate.exists():
                candidates.append(candidate)
        return candidates
