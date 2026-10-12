import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, Float, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.models.database import Base


class AIRecommendation(Base):
    __tablename__ = "ai_recommendations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    organization_id = Column(UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    project_id = Column(UUID(as_uuid=True), ForeignKey("projects.id", ondelete="CASCADE"), nullable=True)
    recommendation_type = Column(String(100), nullable=False)
    # Types: team_recommendation, workload_balance, risk_analysis, sprint_plan, prd_generation
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    confidence_score = Column(Float, default=0.0)
    model_used = Column(String(100), nullable=True)
    tokens_used = Column(Float, default=0.0)
    created_by_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="ai_recommendations")
