"""Initial database schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-10-12 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. StudentProfile
    op.create_table(
        'student_profiles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # 2. StudyPreference
    op.create_table(
        'study_preferences',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profile_id', sa.Integer(), sa.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('preferred_session_minutes', sa.Integer(), nullable=False, server_default='45'),
        sa.Column('break_duration_minutes', sa.Integer(), nullable=False, server_default='15'),
        sa.Column('maximum_daily_study_minutes', sa.Integer(), nullable=False, server_default='240'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )

    # 3. AvailabilityWindow
    op.create_table(
        'availability_windows',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profile_id', sa.Integer(), sa.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day_of_week', sa.Integer(), nullable=False),
        sa.Column('start_time', sa.String(length=5), nullable=False),
        sa.Column('end_time', sa.String(length=5), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true())
    )
    op.create_index('ix_availability_windows_profile_id', 'availability_windows', ['profile_id'])

    # 4. Subject
    op.create_table(
        'subjects',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profile_id', sa.Integer(), sa.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('color', sa.String(length=20), nullable=False, server_default='#3B82F6'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_subjects_profile_id', 'subjects', ['profile_id'])

    # 5. Task
    op.create_table(
        'tasks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('profile_id', sa.Integer(), sa.ForeignKey('student_profiles.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id', ondelete='RESTRICT'), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('task_type', sa.String(length=50), nullable=False, server_default='assignment'),
        sa.Column('due_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('earliest_start_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('estimated_duration_minutes', sa.Integer(), nullable=False),
        sa.Column('priority', sa.String(length=20), nullable=False, server_default='Medium'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='Pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_tasks_profile_id', 'tasks', ['profile_id'])
    op.create_index('ix_tasks_subject_id', 'tasks', ['subject_id'])
    op.create_index('ix_tasks_due_at', 'tasks', ['due_at'])

    # 6. StudySession
    op.create_table(
        'study_sessions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='Scheduled'),
        sa.Column('actual_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_study_sessions_task_id', 'study_sessions', ['task_id'])
    op.create_index('ix_study_sessions_start_at', 'study_sessions', ['start_at'])

    # 7. Recommendation
    op.create_table(
        'recommendations',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('task_id', sa.Integer(), sa.ForeignKey('tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('recommended_start_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('recommended_end_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('suitability_score', sa.Float(), nullable=True),
        sa.Column('model_version', sa.String(length=50), nullable=False, server_default='v1.0'),
        sa.Column('explanation', sa.Text(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='Pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_recommendations_task_id', 'recommendations', ['task_id'])

    # 8. RecommendationFeedback
    op.create_table(
        'recommendation_feedback',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('recommendation_id', sa.Integer(), sa.ForeignKey('recommendations.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('feedback_note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False)
    )
    op.create_index('ix_recommendation_feedback_recommendation_id', 'recommendation_feedback', ['recommendation_id'])


def downgrade() -> None:
    op.drop_table('recommendation_feedback')
    op.drop_table('recommendations')
    op.drop_table('study_sessions')
    op.drop_table('tasks')
    op.drop_table('subjects')
    op.drop_table('availability_windows')
    op.drop_table('study_preferences')
    op.drop_table('student_profiles')
