"""Admin user management endpoints."""

from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_audit_log_service, get_current_superadmin
from app.core.database import get_db
from app.models.audit_log import AuditAction
from app.models.user import User, UserRole
from app.services.audit_log import AuditLogService

router = APIRouter()


class AdminUserResponse(BaseModel):
    id: str
    email: str
    first_name: str | None
    last_name: str | None
    role: str
    permissions: dict | None
    is_active: bool
    created_at: str
    last_login_at: str | None


class InviteAdminRequest(BaseModel):
    email: EmailStr
    role: str = "admin"
    permissions: dict | None = None


class UpdateAdminRequest(BaseModel):
    role: str | None = None
    permissions: dict | None = None
    is_active: bool | None = None


@router.get("", response_model=List[AdminUserResponse])
async def list_admin_users(
    current_user: User = Depends(get_current_superadmin),
    db: AsyncSession = Depends(get_db),
):
    """List all admin users (super_admin and admin roles)."""
    result = await db.execute(
        select(User)
        .where(User.role.in_([UserRole.SUPER_ADMIN, UserRole.ADMIN]))
        .where(User.is_active.is_(True))
        .order_by(User.created_at.desc())
    )
    users = result.scalars().all()

    return [
        AdminUserResponse(
            id=str(u.id),
            email=u.email,
            first_name=u.first_name,
            last_name=u.last_name,
            role=u.role.value,
            permissions=u.permissions,
            is_active=u.is_active,
            created_at=u.created_at.isoformat(),
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
        )
        for u in users
    ]


@router.post("", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
async def invite_admin(
    request: InviteAdminRequest,
    current_user: User = Depends(get_current_superadmin),
    audit_service: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
):
    """
    Invite a new admin by email (pre-registration).
    The invited user will be activated when they first login via OAuth.
    """
    if request.role not in ("super_admin", "admin"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Role must be 'super_admin' or 'admin'",
        )

    # Check if user already exists
    existing = await db.execute(
        select(User).where(User.email == request.email)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists",
        )

    role = UserRole.SUPER_ADMIN if request.role == "super_admin" else UserRole.ADMIN

    user = User(
        email=request.email,
        role=role,
        permissions=request.permissions,
        is_active=True,
        is_admin=True,
        email_verified=False,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    await audit_service.log(
        action=AuditAction.ADMIN_CREATED,
        user=current_user,
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "role": request.role},
    )

    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        permissions=user.permissions,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login_at=None,
    )


@router.put("/{user_id}", response_model=AdminUserResponse)
async def update_admin(
    user_id: str,
    request: UpdateAdminRequest,
    current_user: User = Depends(get_current_superadmin),
    audit_service: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
):
    """Update admin user role or permissions."""
    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if request.role is not None:
        if request.role not in ("super_admin", "admin"):
            raise HTTPException(status_code=400, detail="Invalid role")
        user.role = UserRole.SUPER_ADMIN if request.role == "super_admin" else UserRole.ADMIN

    if request.permissions is not None:
        user.permissions = request.permissions

    if request.is_active is not None:
        user.is_active = request.is_active

    await db.commit()
    await db.refresh(user)

    await audit_service.log(
        action=AuditAction.ADMIN_UPDATED,
        user=current_user,
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email, "changes": request.model_dump(exclude_none=True)},
    )

    return AdminUserResponse(
        id=str(user.id),
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        permissions=user.permissions,
        is_active=user.is_active,
        created_at=user.created_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_admin(
    user_id: str,
    current_user: User = Depends(get_current_superadmin),
    audit_service: AuditLogService = Depends(get_audit_log_service),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate an admin user."""
    try:
        uid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID")

    if uid == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot deactivate yourself")

    result = await db.execute(select(User).where(User.id == uid))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_active = False
    await db.commit()

    await audit_service.log(
        action=AuditAction.ADMIN_DELETED,
        user=current_user,
        resource_type="user",
        resource_id=str(user.id),
        details={"email": user.email},
    )

    return None
