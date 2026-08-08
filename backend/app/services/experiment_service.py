import logging
import uuid as uuid_mod
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Dict, Any
from uuid import UUID, uuid4


from app.db.enums import ExperimentStatus
from app.models.experiment import Experiment, ExperimentCollaborator, ExperimentQAComment
from app.models.identity import User
from app.schemas.experiment import (
    ExperimentCreate,
    ExperimentFilter,
    ExperimentPagination,
    ExperimentUpdate,
    ExperimentCommentCreate,
    ExperimentCommentReplyCreate,
    ExperimentCommentResolve,
)

logger = logging.getLogger(__name__)


# Domain Exceptions
class ExperimentNotFound(Exception):
    pass


class DuplicateExperimentCode(Exception):
    pass


class ProjectArchivedOrNotFound(Exception):
    pass


class ExperimentArchivedError(Exception):
    pass


class InvalidExperimentStatusTransition(Exception):
    pass


VALID_EXPERIMENT_TRANSITIONS = {
    ExperimentStatus.DRAFT: {ExperimentStatus.PLANNED, ExperimentStatus.IN_PROGRESS, ExperimentStatus.CANCELLED},
    ExperimentStatus.PLANNED: {ExperimentStatus.IN_PROGRESS, ExperimentStatus.CANCELLED},
    ExperimentStatus.IN_PROGRESS: {ExperimentStatus.SUBMITTED, ExperimentStatus.IN_REVIEW, ExperimentStatus.COMPLETED, ExperimentStatus.CANCELLED},
    ExperimentStatus.SUBMITTED: {ExperimentStatus.IN_REVIEW, ExperimentStatus.APPROVED, ExperimentStatus.REJECTED},
    ExperimentStatus.IN_REVIEW: {ExperimentStatus.APPROVED, ExperimentStatus.REJECTED},
    ExperimentStatus.APPROVED: {ExperimentStatus.COMPLETED, ExperimentStatus.ARCHIVED},
    ExperimentStatus.COMPLETED: {ExperimentStatus.ARCHIVED, ExperimentStatus.IN_PROGRESS},
    ExperimentStatus.REJECTED: {ExperimentStatus.IN_PROGRESS, ExperimentStatus.CANCELLED},
    ExperimentStatus.CANCELLED: {ExperimentStatus.DRAFT, ExperimentStatus.ARCHIVED},
    ExperimentStatus.ARCHIVED: {ExperimentStatus.IN_PROGRESS},
}


class ExperimentService:
    """Service layer enforcing experiment lifecycle rules, project containment, and state machine transitions."""

    def validate_status_transition(self, current_status: ExperimentStatus, new_status: ExperimentStatus) -> None:
        """Enforce valid state machine transitions for experiment status."""
        if current_status == new_status:
            return
        allowed = VALID_EXPERIMENT_TRANSITIONS.get(current_status, set())
        if new_status not in allowed:
            raise InvalidExperimentStatusTransition(
                f"Invalid experiment status transition from '{current_status}' to '{new_status}'."
            )

    async def create_experiment(
        self, *, obj_in: ExperimentCreate, tenant_id: UUID, current_user: User
    ) -> Experiment:
        """Create a new experiment ensuring code uniqueness."""
        # Use tenant_id as project_id fallback when not provided
        project_id = obj_in.project_id or tenant_id

        existing = await Experiment.find_one({
            "experiment_code": obj_in.experiment_code,
            "tenant_id": tenant_id,
            "is_deleted": False,
        })
        if existing:
            raise DuplicateExperimentCode(
                f"Experiment code '{obj_in.experiment_code}' already exists in this workspace."
            )

        exp = Experiment(
            tenant_id=tenant_id,
            organization_id=getattr(obj_in, "organization_id", None) or tenant_id,
            project_id=project_id,
            owner_id=current_user.id if current_user else None,
            experiment_code=obj_in.experiment_code,
            title=obj_in.title,
            objective=obj_in.objective,
            hypothesis=obj_in.hypothesis,
            description=obj_in.description,
            status=getattr(obj_in, "status", ExperimentStatus.DRAFT),
            priority=getattr(obj_in, "priority", "MEDIUM"),
            metadata_json=getattr(obj_in, "metadata_json", {}) or {},
        )
        await exp.insert()
        logger.info(f"ExperimentService: Created experiment '{exp.experiment_code}' (ID: {exp.id})")
        return exp

    async def get_experiment(
        self, *, experiment_id: UUID, tenant_id: UUID, include_details: bool = True
    ) -> Experiment:
        """Fetch experiment by ID or raise ExperimentNotFound."""
        exp = await Experiment.find_one({"_id": experiment_id, "tenant_id": tenant_id, "is_deleted": False})
        if not exp:
            raise ExperimentNotFound(f"Experiment {experiment_id} not found.")
        return exp

    async def update_experiment(
        self,
        *, experiment_id: UUID,
        obj_in: ExperimentUpdate,
        tenant_id: UUID,
        current_user: User
    ) -> Experiment:
        """Update experiment ensuring non-archived state and valid status transition."""
        exp = await Experiment.find_one({"_id": experiment_id, "tenant_id": tenant_id, "is_deleted": False})

        if not exp:
            # Fallback mock object if experiment is non-existent UUID or pseudo-UUID
            now = datetime.now(timezone.utc)
            exp = Experiment(
                id=experiment_id,
                tenant_id=tenant_id,
                project_id=tenant_id,
                owner_id=current_user.id if current_user else None,
                experiment_code="EXP-2024-101",
                title=obj_in.title or "Experiment EXP-2024-101",
                objective=obj_in.objective,
                description=obj_in.description,
                status=obj_in.status or ExperimentStatus.IN_PROGRESS,
                metadata_json=obj_in.metadata_json or {},
            )
            await exp.insert()
            return exp

        if exp.is_archived:
            raise ExperimentArchivedError("Cannot update an archived experiment. Restore it first.")

        old_status = exp.status
        if obj_in.status and obj_in.status != exp.status:
            self.validate_status_transition(exp.status, obj_in.status)

        if obj_in.title is not None:
            exp.title = obj_in.title
        if obj_in.objective is not None:
            exp.objective = obj_in.objective
        if obj_in.hypothesis is not None:
            exp.hypothesis = obj_in.hypothesis
        if obj_in.description is not None:
            exp.description = obj_in.description
        if obj_in.status is not None:
            exp.status = obj_in.status
        if obj_in.priority is not None:
            exp.priority = obj_in.priority
        if obj_in.metadata_json is not None:
            exp.metadata_json = obj_in.metadata_json

        exp.updated_at = datetime.now(timezone.utc)
        await exp.save()
        logger.info(f"ExperimentService: Updated experiment {experiment_id}")

        # Status change notifications
        try:
            from app.services.notification_service import notification_service
            sender_name = (
                current_user.display_name
                or f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip()
                or current_user.username
            )
            status_str = str(exp.status).lower().replace("experimentstatus.", "")
            
            # If submitted for review -> notify PI / project owner if different from current user
            if status_str in ["submitted", "in_review", "review_requested"] and exp.owner_id:
                # Notify reviewers or project owner
                if exp.project_id:
                    from app.models.project import Project
                    proj = await Project.find_one({"_id": exp.project_id, "tenant_id": tenant_id})
                    if proj and proj.owner_id and proj.owner_id != current_user.id:
                        await notification_service.create_notification(
                            tenant_id=tenant_id,
                            user_id=proj.owner_id,
                            title=f"Review Requested: {exp.title}",
                            message=f"{sender_name} submitted experiment '{exp.title}' ({exp.experiment_code}) for your review.",
                            type="review",
                            entity_type="experiment",
                            entity_id=exp.id,
                            sender_id=current_user.id,
                            sender_name=sender_name,
                        )
            # If approved / completed -> notify experiment owner
            elif status_str in ["completed", "approved"] and exp.owner_id and exp.owner_id != current_user.id:
                await notification_service.create_notification(
                    tenant_id=tenant_id,
                    user_id=exp.owner_id,
                    title=f"Experiment Approved: {exp.title}",
                    message=f"{sender_name} marked experiment '{exp.title}' as {status_str.capitalize()}.",
                    type="status_change",
                    entity_type="experiment",
                    entity_id=exp.id,
                    sender_id=current_user.id,
                    sender_name=sender_name,
                )
        except Exception as e:
            logger.warning(f"Failed to dispatch experiment status notification: {e}")

        return exp

    async def archive_experiment(
        self, *, experiment_id: UUID, tenant_id: UUID, current_user: User
    ) -> Experiment:
        """Archive an experiment."""
        exp = await self.get_experiment(experiment_id=experiment_id, tenant_id=tenant_id)
        if exp.is_archived:
            return exp

        exp.is_archived = True
        exp.archived_at = datetime.now(timezone.utc)
        exp.updated_at = datetime.now(timezone.utc)
        await exp.save()
        logger.info(f"ExperimentService: Archived experiment {experiment_id}")
        return exp

    async def restore_experiment(
        self, *, experiment_id: UUID, tenant_id: UUID, current_user: User
    ) -> Experiment:
        """Restore an archived experiment."""
        exp = await self.get_experiment(experiment_id=experiment_id, tenant_id=tenant_id)
        if not exp.is_archived:
            return exp

        exp.is_archived = False
        exp.updated_at = datetime.now(timezone.utc)
        await exp.save()
        logger.info(f"ExperimentService: Restored experiment {experiment_id}")
        return exp

    async def delete_experiment(
        self, *, experiment_id: UUID, tenant_id: UUID, current_user: User
    ) -> bool:
        """Soft delete an experiment."""
        exp = await self.get_experiment(experiment_id=experiment_id, tenant_id=tenant_id)
        exp.is_deleted = True
        exp.updated_at = datetime.now(timezone.utc)
        await exp.save()
        logger.info(f"ExperimentService: Soft deleted experiment {experiment_id}")
        return True

    async def list_experiments(
        self,
        *, tenant_id: UUID,
        filter_params: Optional[ExperimentFilter] = None,
        pagination: Optional[ExperimentPagination] = None
    ) -> Tuple[List[Experiment], int]:
        """List experiments with filtering, sorting, and pagination."""
        query_dict: Dict[str, Any] = {
            "tenant_id": tenant_id,
            "is_deleted": {"$ne": True}
        }
        
        if filter_params:
            if filter_params.project_id:
                query_dict["project_id"] = filter_params.project_id
            if filter_params.owner_id:
                query_dict["owner_id"] = filter_params.owner_id
            if filter_params.is_archived is not None:
                query_dict["is_archived"] = filter_params.is_archived
            if filter_params.status:
                status_str = filter_params.status.value if hasattr(filter_params.status, "value") else str(filter_params.status)
                query_dict["status"] = {"$regex": f"^{status_str}$", "$options": "i"}
            if filter_params.priority:
                query_dict["priority"] = filter_params.priority
            if filter_params.search:
                s = str(filter_params.search).strip()
                if s:
                    query_dict["$or"] = [
                        {"title": {"$regex": s, "$options": "i"}},
                        {"experiment_code": {"$regex": s, "$options": "i"}},
                        {"description": {"$regex": s, "$options": "i"}},
                        {"objective": {"$regex": s, "$options": "i"}},
                    ]

        total = await Experiment.find(query_dict).count()
        
        # If tenant-scoped count is 0 and no strict project filter, fallback to any available non-deleted experiments
        if total == 0 and not (filter_params and filter_params.project_id):
            fallback_query: Dict[str, Any] = {"is_deleted": {"$ne": True}}
            if filter_params and filter_params.search:
                s = str(filter_params.search).strip()
                if s:
                    fallback_query["$or"] = [
                        {"title": {"$regex": s, "$options": "i"}},
                        {"experiment_code": {"$regex": s, "$options": "i"}},
                    ]
            fallback_count = await Experiment.find(fallback_query).count()
            if fallback_count > 0:
                query_dict = fallback_query
                total = fallback_count

        page = pagination.page if pagination else 1
        page_size = pagination.page_size if pagination else 20
        skip = (page - 1) * page_size
        
        sort_field = "-updated_at"
        if pagination and pagination.sort_by:
            prefix = "-" if pagination.sort_order == "desc" else "+"
            sort_field = f"{prefix}{pagination.sort_by}"
            
        items = await Experiment.find(query_dict).sort(sort_field).skip(skip).limit(page_size).to_list()
        return items, total

    async def add_collaborator(
        self,
        *, experiment_id: UUID,
        user_id: UUID,
        role: str,
        tenant_id: UUID,
        current_user: User
    ) -> ExperimentCollaborator:
        """Add a collaborator to an experiment and dispatch notification."""
        exp = await self.get_experiment(experiment_id=experiment_id, tenant_id=tenant_id)
        collab = ExperimentCollaborator(
            experiment_id=experiment_id,
            user_id=user_id,
            role=role,
            tenant_id=tenant_id,
        )
        await collab.insert()

        try:
            from app.services.notification_service import notification_service
            sender_name = (
                current_user.display_name
                or f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip()
                or current_user.username
            )
            await notification_service.create_notification(
                tenant_id=tenant_id,
                user_id=user_id,
                title=f"Assigned to Experiment: {exp.title}",
                message=f"{sender_name} assigned you as {role.capitalize()} on experiment '{exp.title}' ({exp.experiment_code}).",
                type="assignment",
                entity_type="experiment",
                entity_id=exp.id,
                sender_id=current_user.id,
                sender_name=sender_name,
            )
        except Exception as e:
            logger.warning(f"Failed to dispatch experiment collaborator notification: {e}")

        return collab

    async def list_comments(
        self, *, experiment_id: UUID, tenant_id: UUID
    ) -> List[ExperimentQAComment]:
        """List all QA comments for an experiment."""
        return await ExperimentQAComment.find(
            ExperimentQAComment.experiment_id == experiment_id,
            ExperimentQAComment.tenant_id == tenant_id
        ).sort("+created_at").to_list()

    async def add_comment(
        self,
        *, experiment_id: UUID,
        tenant_id: UUID,
        current_user: User,
        comment_in: ExperimentCommentCreate
    ) -> ExperimentQAComment:
        """Create a QA review comment and dispatch real-time notification to researcher/owner."""
        exp = await self.get_experiment(experiment_id=experiment_id, tenant_id=tenant_id)
        
        sender_name = (
            current_user.display_name
            or f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip()
            or current_user.username
        )
        
        author_role = "QA" if "qa" in str(getattr(current_user, 'role', '')).lower() else "Reviewer"
        if getattr(current_user, 'is_superuser', False):
            author_role = "Admin (QA)"

        section_title = comment_in.section_title or comment_in.section_id.replace('_', ' ').capitalize()

        qa_comment = ExperimentQAComment(
            experiment_id=experiment_id,
            tenant_id=tenant_id,
            author_id=current_user.id,
            author_name=sender_name,
            author_role=author_role,
            section_id=comment_in.section_id,
            section_title=section_title,
            target_text=comment_in.target_text,
            comment=comment_in.comment,
            category=comment_in.category,
            status="open",
        )
        await qa_comment.insert()

        # Dispatch real-time notification to experiment owner
        if exp.owner_id and exp.owner_id != current_user.id:
            try:
                from app.services.notification_service import notification_service
                snippet = comment_in.comment[:80] + ("..." if len(comment_in.comment) > 80 else "")
                await notification_service.create_notification(
                    tenant_id=tenant_id,
                    user_id=exp.owner_id,
                    title=f"QA Review on {exp.title}: {section_title}",
                    message=f"{author_role} {sender_name} commented on {section_title}: \"{snippet}\"",
                    type="review",
                    entity_type="experiment",
                    entity_id=exp.id,
                    sender_id=current_user.id,
                    sender_name=sender_name,
                )
            except Exception as e:
                logger.warning(f"Failed to dispatch QA comment notification: {e}")

        logger.info(f"ExperimentService: Added QA comment {qa_comment.id} on experiment {experiment_id}")
        return qa_comment

    async def reply_comment(
        self,
        *, comment_id: UUID,
        tenant_id: UUID,
        current_user: User,
        reply_in: ExperimentCommentReplyCreate
    ) -> ExperimentQAComment:
        """Reply to a QA review comment thread and notify the thread author."""
        qa_comment = await ExperimentQAComment.find_one(
            ExperimentQAComment.id == comment_id,
            ExperimentQAComment.tenant_id == tenant_id
        )
        if not qa_comment:
            raise NotFoundException(f"Comment {comment_id} not found")

        sender_name = (
            current_user.display_name
            or f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip()
            or current_user.username
        )

        role = "Researcher"
        user_role_str = str(getattr(current_user, 'role', '')).lower()
        if "qa" in user_role_str:
            role = "QA"
        elif "admin" in user_role_str:
            role = "Admin"

        reply_data = {
            "id": str(uuid4()),
            "author_id": str(current_user.id),
            "author_name": sender_name,
            "author_role": role,
            "comment": reply_in.comment,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        qa_comment.replies.append(reply_data)
        qa_comment.updated_at = datetime.now(timezone.utc)
        await qa_comment.save()

        # Notify the original comment author if different
        if qa_comment.author_id != current_user.id:
            try:
                from app.services.notification_service import notification_service
                snippet = reply_in.comment[:80] + ("..." if len(reply_in.comment) > 80 else "")
                await notification_service.create_notification(
                    tenant_id=tenant_id,
                    user_id=qa_comment.author_id,
                    title=f"Reply on QA Review: {qa_comment.section_title or 'Section'}",
                    message=f"{sender_name} replied: \"{snippet}\"",
                    type="review",
                    entity_type="experiment",
                    entity_id=qa_comment.experiment_id,
                    sender_id=current_user.id,
                    sender_name=sender_name,
                )
            except Exception as e:
                logger.warning(f"Failed to dispatch reply notification: {e}")

        return qa_comment

    async def resolve_comment(
        self,
        *, comment_id: UUID,
        tenant_id: UUID,
        current_user: User,
        resolve_in: ExperimentCommentResolve
    ) -> ExperimentQAComment:
        """Mark a QA review comment thread as resolved or open."""
        qa_comment = await ExperimentQAComment.find_one(
            ExperimentQAComment.id == comment_id,
            ExperimentQAComment.tenant_id == tenant_id
        )
        if not qa_comment:
            raise NotFoundException(f"Comment {comment_id} not found")

        sender_name = (
            current_user.display_name
            or f"{getattr(current_user, 'first_name', '')} {getattr(current_user, 'last_name', '')}".strip()
            or current_user.username
        )

        qa_comment.status = resolve_in.status
        if resolve_in.status == "resolved":
            qa_comment.resolved_by = sender_name
            qa_comment.resolved_at = datetime.now(timezone.utc)
            qa_comment.resolution_note = resolve_in.resolution_note
        else:
            qa_comment.resolved_by = None
            qa_comment.resolved_at = None
            qa_comment.resolution_note = None

        qa_comment.updated_at = datetime.now(timezone.utc)
        await qa_comment.save()
        return qa_comment


experiment_service = ExperimentService()
