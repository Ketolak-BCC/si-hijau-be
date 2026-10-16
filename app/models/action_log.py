from datetime import datetime, timezone

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ActionLog(Base):
    __tablename__ = "action_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    scan_id: Mapped[int | None] = (
        mapped_column(Integer, ForeignKey("scans_histories.id", ondelete="SET NULL"), nullable=True)
        if False
        else mapped_column(Integer, ForeignKey("scan_histories.id", ondelete="SET NULL"), nullable=True)
    )
    action_type: Mapped[str] = mapped_column(String(50), nullable=False)
    waste_category: Mapped[str] = mapped_column(String(50), nullable=False)
    partner_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("partners.id", ondelete="SET NULL"), nullable=True
    )
    quantity_desc: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False
    )

    user = relationship("User", back_populates="action_logs")
    scan = relationship("ScanHistory", back_populates="action_logs")
    partner = relationship("Partner", back_populates="action_logs")
