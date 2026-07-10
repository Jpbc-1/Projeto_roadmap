"""
Modelos ORM (SQLAlchemy) do Roadmap AI.

Organizado nos 3 domínios definidos na modelagem:
  1. Core (Jornada e Planejamento): User, Goal, Roadmap, RoadmapChapter, Mission
  2. Execução e Diário: MissionExecution
  3. Gamificação: UserStats, Achievement, UserAchievement

Nota de arquitetura: para o MVP, os modelos ORM abaixo são usados diretamente
como estrutura de persistência. Se no futuro a lógica de negócio do domínio
ficar complexa o suficiente para exigir entidades desacopladas do SQLAlchemy
(puro Python, sem depender do ORM), podemos introduzir uma camada de mapeamento
entre `domain/entities` (puras) e este módulo — mas isso seria complexidade
prematura para o estágio atual do projeto.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base



class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goals: Mapped[list["Goal"]] = relationship(back_populates="user")
    stats: Mapped[Optional["UserStats"]] = relationship(back_populates="user", uselist=False)
    achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user")


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    context_prompt: Mapped[str] = mapped_column(Text)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  # active | achieved | dropped
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="goals")
    roadmaps: Mapped[list["Roadmap"]] = relationship(back_populates="goal")


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_generation_log: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goal: Mapped["Goal"] = relationship(back_populates="roadmaps")
    chapters: Mapped[list["RoadmapChapter"]] = relationship(back_populates="roadmap")


class RoadmapChapter(Base):
    __tablename__ = "roadmap_chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    order_index: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="locked")  # locked | in_progress | completed

    roadmap: Mapped["Roadmap"] = relationship(back_populates="chapters")
    missions: Mapped[list["Mission"]] = relationship(back_populates="chapter")


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("roadmap_chapters.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer)

    chapter: Mapped["RoadmapChapter"] = relationship(back_populates="missions")
    executions: Mapped[list["MissionExecution"]] = relationship(back_populates="mission")


class MissionExecution(Base):
    __tablename__ = "mission_executions"

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), index=True)
    # user_id duplicado aqui de propósito: evita JOINs caros (mission -> chapter
    # -> roadmap -> goal -> user) para queries frequentes como "XP diário do usuário".
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    xp_rewarded: Mapped[int] = mapped_column(Integer, default=0)
    user_reflection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    mission: Mapped["Mission"] = relationship(back_populates="executions")



class UserStats(Base):
    __tablename__ = "user_stats"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="stats")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_condition: Mapped[str] = mapped_column(String(100))  # ex: "7_day_streak"
    icon_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    unlocked_by: Mapped[list["UserAchievement"]] = relationship(back_populates="achievement")


class UserAchievement(Base):
    __tablename__ = "user_achievements"
    __table_args__ = (UniqueConstraint("user_id", "achievement_id", name="uq_user_achievement"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    achievement_id: Mapped[int] = mapped_column(ForeignKey("achievements.id"), index=True)
    unlocked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="achievements")
    achievement: Mapped["Achievement"] = relationship(back_populates="unlocked_by")
