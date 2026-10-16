from sqladmin import ModelView

from app.models.action_log import ActionLog
from app.models.guide import ProcessingGuide
from app.models.partner import Partner
from app.models.scan import ScanHistory
from app.models.user import User


class UserAdmin(ModelView, model=User):
    column_list = [
        User.id,
        User.email,
        User.full_name,
        User.role,
        User.auth_provider,
        User.has_yard,
        User.free_time_level,
        User.is_active,
    ]
    column_searchable_list = [User.email, User.full_name]
    column_sortable_list = [User.id, User.email, User.created_at]
    icon = "fa-solid fa-user"


class PartnerAdmin(ModelView, model=Partner):
    column_list = [
        Partner.id,
        Partner.name,
        Partner.accepted_categories,
        Partner.phone_number,
        Partner.operational_hours,
        Partner.is_active,
    ]
    column_searchable_list = [Partner.name, Partner.address, Partner.accepted_categories]
    column_sortable_list = [Partner.id, Partner.name, Partner.created_at]
    icon = "fa-solid fa-handshake"


class ProcessingGuideAdmin(ModelView, model=ProcessingGuide):
    column_list = [
        ProcessingGuide.id,
        ProcessingGuide.waste_category,
        ProcessingGuide.title,
        ProcessingGuide.difficulty,
        ProcessingGuide.estimated_time,
    ]
    column_searchable_list = [ProcessingGuide.title, ProcessingGuide.waste_category]
    icon = "fa-solid fa-book"


class ScanHistoryAdmin(ModelView, model=ScanHistory):
    column_list = [
        ScanHistory.id,
        ScanHistory.user_id,
        ScanHistory.item_name,
        ScanHistory.detected_category,
        ScanHistory.confidence_score,
        ScanHistory.created_at,
    ]
    column_searchable_list = [ScanHistory.item_name, ScanHistory.detected_category]
    column_sortable_list = [ScanHistory.id, ScanHistory.created_at]
    can_create = False
    icon = "fa-solid fa-qrcode"


class ActionLogAdmin(ModelView, model=ActionLog):
    column_list = [
        ActionLog.id,
        ActionLog.user_id,
        ActionLog.action_type,
        ActionLog.waste_category,
        ActionLog.partner_id,
        ActionLog.created_at,
    ]
    column_sortable_list = [ActionLog.id, ActionLog.created_at]
    can_create = False
    icon = "fa-solid fa-chart-line"
