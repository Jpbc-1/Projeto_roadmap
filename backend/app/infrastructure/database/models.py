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

from datetime import date, datetime, time
from typing import Optional
from sqlalchemy import Column, Boolean

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    Time,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infrastructure.database.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(30), unique=True, index=True, nullable=True)
    password_hash: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    plan: Mapped[str] = mapped_column(String(20), default="free")
    credits_remaining: Mapped[int] = mapped_column(Integer, default=500)

    timezone: Mapped[str] = mapped_column(String(50), default="America/Sao_Paulo")

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goals: Mapped[list["Goal"]] = relationship(back_populates="user")
    stats: Mapped[Optional["UserStats"]] = relationship(back_populates="user", uselist=False)
    achievements: Mapped[list["UserAchievement"]] = relationship(back_populates="user")
    push_tokens: Mapped[list["UserPushToken"]] = relationship(back_populates="user", cascade="all, delete-orphan")

    email_verified = Column(Boolean, default=False, server_default="false", nullable=False)


class Goal(Base):
    __tablename__ = "goals"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    context_prompt: Mapped[str] = mapped_column(Text)
    target_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active")  


    category: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    involves_learning: Mapped[bool] = mapped_column(Boolean, default=False)


    weekly_active_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True) 
    daily_time_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    prior_knowledge_level: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)

    estimated_completion_weeks: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    generation_status: Mapped[str] = mapped_column(String(20), default="pending")
    generation_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    improved_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    pending_questions: Mapped[Optional[list]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="goals")
    roadmaps: Mapped[list["Roadmap"]] = relationship(back_populates="goal")
    recommendations: Mapped[list["GoalRecommendation"]] = relationship(back_populates="goal")


class Roadmap(Base):
    __tablename__ = "roadmaps"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    version: Mapped[int] = mapped_column(Integer, default=1)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    ai_generation_log: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    last_adapted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    pending_adaptation: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goal: Mapped["Goal"] = relationship(back_populates="roadmaps")
    chapters: Mapped[list["RoadmapChapter"]] = relationship(
        back_populates="roadmap", order_by="RoadmapChapter.order_index"
    )


class RoadmapChapter(Base):
    __tablename__ = "roadmap_chapters"

    id: Mapped[int] = mapped_column(primary_key=True)
    roadmap_id: Mapped[int] = mapped_column(ForeignKey("roadmaps.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    order_index: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(20), default="locked")  
    closed_early: Mapped[bool] = mapped_column(Boolean, default=False)

    created_by: Mapped[str] = mapped_column(String(10), default="ai")

    is_locked_from_ai: Mapped[bool] = mapped_column(Boolean, default=False)

    roadmap: Mapped["Roadmap"] = relationship(back_populates="chapters")
    missions: Mapped[list["Mission"]] = relationship(back_populates="chapter", order_by="Mission.order_index")


class Mission(Base):
    __tablename__ = "missions"

    id: Mapped[int] = mapped_column(primary_key=True)
    chapter_id: Mapped[int] = mapped_column(ForeignKey("roadmap_chapters.id"), index=True)
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    estimated_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer)

    created_by: Mapped[str] = mapped_column(String(10), default="ai")

    is_conceptual: Mapped[bool] = mapped_column(Boolean, default=True)

    chapter: Mapped["RoadmapChapter"] = relationship(back_populates="missions")
    executions: Mapped[list["MissionExecution"]] = relationship(back_populates="mission")

class MissionExecution(Base):
    __tablename__ = "mission_executions"
    __table_args__ = (UniqueConstraint("mission_id", "user_id", name="uq_mission_execution_user"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    mission_id: Mapped[int] = mapped_column(ForeignKey("missions.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    xp_rewarded: Mapped[int] = mapped_column(Integer, default=0)
    user_reflection: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    ai_feedback: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    difficulty_rating: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    satisfaction_rating: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    mission: Mapped["Mission"] = relationship(back_populates="executions")



class UserStats(Base):
    __tablename__ = "user_stats"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0)
    current_level: Mapped[int] = mapped_column(Integer, default=1)
    current_streak: Mapped[int] = mapped_column(Integer, default=0)
    max_streak: Mapped[int] = mapped_column(Integer, default=0)
    last_activity_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    last_bonus_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)

    user: Mapped["User"] = relationship(back_populates="stats")


class Achievement(Base):
    __tablename__ = "achievements"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    required_condition: Mapped[str] = mapped_column(String(100)) 
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



class KnowledgeNode(Base):
    """Um CONCEITO identificado pela extração do Mapa do Conhecimento (ver
    app/application/flashcards/extract_concepts.py) -- só o metadado do
    conceito em si (nome + embedding, pra dedup semântico entre extrações
    diferentes do mesmo goal), não o material de revisão.

    NÃO tem mais estado de repetição espaçada aqui (antes tinha
    next_review_date/interval_days/easiness_factor/repetition_count) --
    isso agora vive em Flashcard, que é a unidade de fato revisável e pode
    nem existir pra este node (se importance_score < FLASHCARD_MIN_IMPORTANCE,
    ver extract_concepts.py) ou pode ser rejeitada pela pessoa na tela de
    aprovação (ver Flashcard.status == "pending_review")."""

    __tablename__ = "knowledge_nodes"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    mission_id: Mapped[Optional[int]] = mapped_column(ForeignKey("missions.id"), nullable=True, index=True)
    topic_name: Mapped[str] = mapped_column(String(255))
    embedding: Mapped[list] = mapped_column(JSON)
    importance_score: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Deck(Base):
    """Agrupamento de flashcards. Toda conta tem exatamente 1 baralho
    principal (is_main=True), criado sob demanda na primeira vez que a
    pessoa precisa dele (ver get_or_create_main_deck em
    app/application/flashcards/deck_provisioning.py) -- não no cadastro,
    pra não criar uma linha morta pra quem nunca chega a usar a área de
    revisões.

    is_main é único por usuário (ver unique index parcial na migration) --
    é o baralho que os flashcards aprovados da extração de IA caem por
    padrão, e o ÚNICO que conta pro streak/bônus diário (ver
    answer_review.py) -- baralhos extra que a pessoa criar por conta
    própria são pra organização pessoal, sem pressão de sequência."""

    __tablename__ = "decks"
    __table_args__ = (
        Index("ix_decks_user_id_is_main_unique", "user_id", unique=True, postgresql_where=text("is_main = true")),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    name: Mapped[str] = mapped_column(String(100))
    is_main: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    flashcards: Mapped[list["Flashcard"]] = relationship(back_populates="deck", cascade="all, delete-orphan")


class Flashcard(Base):
    """A unidade revisável de verdade -- pergunta (front) + resposta
    (back) + estado da repetição espaçada. Pode nascer de duas formas:
    extraída pela IA a partir de um KnowledgeNode importante (
    knowledge_node_id preenchido) ou criada manualmente pela pessoa
    (knowledge_node_id NULL).

    status:
    - "pending_review": a IA gerou este candidato, mas a pessoa ainda não
      decidiu se quer ele no baralho de verdade (ver tela de aprovação em
      GET /flashcards/pending) -- due/fsrs_state ainda não têm sentido
      real aqui, o card não está "agendado" pra nada ainda.
    - "active": aprovado (ou criado manualmente), sendo revisado de
      verdade -- entra em GET /flashcards/due quando due <= agora.
    - "graduated": a pessoa acertou fácil repetidamente (ver
      consecutive_easy_count/EASY_STREAK_TO_GRADUATE em answer_review.py)
      -- some da rotina de revisão, mas fica salvo (histórico, e dá pra
      reativar) em vez de apagado. Apagar de vez é uma ação separada e
      explícita (DELETE /flashcards/{id}), não automática.

    Campos fsrs_state/fsrs_step/stability/difficulty/due/last_review_at
    espelham exatamente fsrs.Card (ver app/application/flashcards/
    scheduler.py) -- não são um formato próprio: é literalmente o que a
    biblioteca precisa pra reconstruir o Card na próxima revisão, salvo
    campo a campo."""

    __tablename__ = "flashcards"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    deck_id: Mapped[int] = mapped_column(ForeignKey("decks.id"), index=True)
    knowledge_node_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("knowledge_nodes.id"), nullable=True, index=True
    )
    front: Mapped[str] = mapped_column(Text)
    back: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="active", index=True)


    fsrs_state: Mapped[str] = mapped_column(String(15), default="learning")
    fsrs_step: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    stability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    difficulty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    due: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    last_review_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    consecutive_easy_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    deck: Mapped["Deck"] = relationship(back_populates="flashcards")


class FlashcardReview(Base):
    """Log de auditoria de cada resposta de revisão -- old/new stability e
    old/new difficulty são os dois parâmetros centrais do FSRS (ver
    docstring de Flashcard), aqui preservados por linha pra dar pra
    reconstruir a evolução de um card ao longo do tempo (e, no futuro,
    treinar pesos personalizados por usuário -- o próprio pacote fsrs
    suporta isso a partir do review log, mas exige um volume de revisões
    que não faz sentido tentar prematuramente, ver scheduler.py)."""

    __tablename__ = "flashcard_reviews"

    id: Mapped[int] = mapped_column(primary_key=True)
    flashcard_id: Mapped[int] = mapped_column(ForeignKey("flashcards.id"), index=True)
    reviewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    rating: Mapped[str] = mapped_column(String(10))  
    old_stability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_stability: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    old_difficulty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    new_difficulty: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    elapsed_days: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)


class GoalRecommendation(Base):
    """Recurso (app, curso, livro, comunidade, ferramenta) que a IA sugere
    como complemento pra ajudar a alcançar o objetivo -- gerado junto com o
    roadmap inicial. De propósito SEM campo de URL: a IA não tem como saber
    se um link específico existe/está certo, e link quebrado/errado é pior
    que não ter link nenhum. name + description já dão o suficiente pra
    pessoa procurar por conta própria."""

    __tablename__ = "goal_recommendations"

    id: Mapped[int] = mapped_column(primary_key=True)
    goal_id: Mapped[int] = mapped_column(ForeignKey("goals.id"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    description: Mapped[str] = mapped_column(Text)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    goal: Mapped["Goal"] = relationship(back_populates="recommendations")


class BackgroundJob(Base):
    """Fila de tarefas em background (geração de roadmap, adaptação
    automática, extração do Mapa do Conhecimento) persistida no Postgres --
    substitui o uso de FastAPI BackgroundTasks puro, que perde a tarefa se o
    processo cair no meio do trabalho e não tem retry nem visibilidade
    nenhuma. Processada por um worker simples via polling, sem precisar de
    infra nova (Redis/Celery) -- ver app/core/jobs/worker.py."""

    __tablename__ = "background_jobs"

    id: Mapped[int] = mapped_column(primary_key=True)
    job_type: Mapped[str] = mapped_column(String(50), index=True)
    payload: Mapped[dict] = mapped_column(JSON)
    status: Mapped[str] = mapped_column(String(20), default="pending", index=True)
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=3)
    run_after: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    locked_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_error: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class AIUsageLog(Base):
    """Uma linha por chamada de IA bem-sucedida -- não é usado pra cobrar
    (isso é feito por créditos fixos por ação, ver User.credits_remaining e
    CREDITS_COST_* em config.py), é só telemetria: quanto token cada tipo
    de ação realmente consome, pra calibrar o custo em créditos com dado
    real antes de lançar de verdade (em vez de só chutar um número)."""

    __tablename__ = "ai_usage_logs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(50), index=True)
    model: Mapped[str] = mapped_column(String(50))
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class OAuthAccount(Base):
    """Vínculo entre um User e uma conta de provider externo (Google,
    Facebook, e Apple como candidato óbvio depois -- ver docs/adr). Tabela
    separada em vez de colunas soltas (google_id, facebook_id, ...) direto
    em User porque uma pessoa pode vincular MAIS de um provider à mesma
    conta (ex: cadastrou com Google, depois também quer entrar com
    Facebook) -- N colunas nullable não escala bem toda vez que um
    provider novo entra, uma linha nova nessa tabela escala.

    provider_user_id é o "sub" do Google ou o "id" do Facebook -- o
    identificador que O PROVIDER garante ser estável e único pra aquela
    pessoa, não o e-mail (e-mail pode mudar; esse id não muda)."""

    __tablename__ = "oauth_accounts"
    __table_args__ = (UniqueConstraint("provider", "provider_user_id", name="uq_oauth_provider_account"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    provider: Mapped[str] = mapped_column(String(20)) 
    provider_user_id: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))  
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Reminder(Base):
    """Lembrete RECORRENTE e solto (ex: "Lembrete da manhã", 08:00, todo
    dia) -- não está preso a um compromisso específico, isso é
    CalendarEvent, logo abaixo. Ver docs/adr/0002 pra por que são dois
    mecanismos separados em vez de um sistema polimórfico único de
    "notifications", e docs/adr/0003 pra essas 3 colunas de preferência.

    IMPORTANTE: time_of_day/days_of_week são "hora de parede" (ex: 8h),
    não um instante absoluto -- o agendador (application/notifications/
    schedule_due_reminders.py) tem que converter usando User.timezone pra
    saber se "agora" bate com isso pra CADA usuário, não usar UTC direto.

    Preferência de notificação (3 escolhas independentes):
    - is_active: já cobre "quer notificação ou não" -- um Reminder inteiro
      É uma notificação, então desligar é o mesmo que "não quero essa".
    - notification_timing_mode: 'app_default' (time_of_day/days_of_week
      preenchidos com um horário sensato, ver core/notification_defaults.py)
      ou 'custom' (a pessoa escolheu o horário e os dias ela mesma).
    - notification_style: 'app_generated' (o texto é montado na hora do
      disparo, olhando o que está pendente -- ver
      domain/services/notification_content.py) ou 'custom_message' (a
      pessoa escreveu o texto, guardado em custom_message).
    """

    __tablename__ = "reminders"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    label: Mapped[str] = mapped_column(String(120))
    time_of_day: Mapped[time] = mapped_column(Time)
    days_of_week: Mapped[list] = mapped_column(JSON)  
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    last_dispatched_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    notification_timing_mode: Mapped[str] = mapped_column(String(20), default="app_default")
    notification_style: Mapped[str] = mapped_column(String(20), default="app_generated")
    custom_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CalendarEvent(Base):
    """Compromisso/evento cadastrado manualmente pelo usuário (ex:
    "Dentista às 15h") -- diferente de Mission, isso não vem da IA, é a
    vida real da pessoa. start_datetime/end_datetime SÃO instantes
    absolutos (tz-aware), diferente do Reminder -- comparar com "agora"
    não precisa de conversão de fuso, o valor já é UTC de verdade.

    Preferência de notificação (mesmas 3 escolhas do Reminder, ver
    docs/adr/0003), mas notify_enabled é campo próprio aqui -- diferente
    do Reminder, um CalendarEvent existe mesmo sem lembrete nenhum (é
    normal só querer registrar o compromisso sem ser avisado).
    """

    __tablename__ = "calendar_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    title: Mapped[str] = mapped_column(String(200))
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    start_datetime: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    end_datetime: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    is_all_day: Mapped[bool] = mapped_column(Boolean, default=False)
    notify_enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    remind_before_minutes: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    notification_timing_mode: Mapped[str] = mapped_column(String(20), default="app_default")
    notification_style: Mapped[str] = mapped_column(String(20), default="app_generated")
    custom_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    reminder_dispatched_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class UserPushToken(Base):
    """Device token (Expo push token) de um aparelho de um usuário -- é
    pra ONDE o handler de disparo (core/jobs/handlers.py, _send_push)
    manda a notificação de verdade (Reminder/CalendarEvent só decidem
    QUANDO e O QUÊ, ver domain/services/notification_content.py; esta
    tabela decide PRA ONDE).

    Uma linha por APARELHO, não por usuário: uma pessoa pode ter vários
    (celular + tablet, por exemplo) -- todos recebem a notificação.

    push_token é unique (não (user_id, push_token)) de propósito: o
    mesmo token físico nunca deveria existir em duas linhas, e isso é o
    que permite o UPSERT do registro (app/application/notifications/
    register_push_token.py) ser "achar por token", não por combinação
    user+token -- resolve token igual chegando de outra conta (troca de
    usuário no mesmo aparelho) sem duplicar nem exigir lógica extra no
    app cliente.
    """

    __tablename__ = "user_push_tokens"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    push_token: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    platform: Mapped[str] = mapped_column(String(10))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="push_tokens")