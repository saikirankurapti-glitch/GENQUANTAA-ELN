import uuid
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.tenant import Tenant
from app.schemas.identity import UserCreate, UserLoginRequest
from app.services.identity.user_service import user_service
from app.services.identity.authentication_service import authentication_service
from app.services.identity.api_key_service import api_key_service
from app.services.identity.electronic_signature_service import electronic_signature_service
from app.services.identity.exceptions import AccountLocked, InvalidCredentials


@pytest.mark.asyncio
async def test_user_registration_and_authentication_workflow(db: AsyncSession):
    """Integration test: Register user -> Authenticate -> Verify session issuance."""
    tenant_id = uuid.uuid4()
    # Create tenant record stub for foreign key constraint if needed
    tenant = Tenant(id=tenant_id, name="Test Lab Tenant", code=f"t_{uuid.uuid4().hex[:6]}")
    db.add(tenant)
    await db.commit()

    user_in = UserCreate(
        username="integration_user",
        email="integration@lab.org",
        first_name="Test",
        last_name="User",
        password="SecurePassword123!",
        tenant_id=tenant_id,
    )
    new_user = await user_service.register_user(db, obj_in=user_in)
    assert new_user.id is not None
    assert new_user.username == "integration_user"

    # Authenticate
    login_req = UserLoginRequest(
        username_or_email="integration_user",
        password="SecurePassword123!",
    )
    user, session_token, refresh_token = await authentication_service.authenticate_user(
        db, tenant_id=tenant_id, credentials=login_req
    )
    assert user.id == new_user.id
    assert len(session_token) > 0
    assert len(refresh_token) > 0


@pytest.mark.asyncio
async def test_account_lockout_after_failed_attempts(db: AsyncSession):
    """Integration test: 5 consecutive failed logins trigger account lockout."""
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="Lockout Lab Tenant", code=f"t_{uuid.uuid4().hex[:6]}")
    db.add(tenant)
    await db.commit()

    user_in = UserCreate(
        username="lockout_target",
        email="lockout@lab.org",
        first_name="Lock",
        last_name="Target",
        password="ValidPassword123!",
        tenant_id=tenant_id,
    )
    user = await user_service.register_user(db, obj_in=user_in)

    wrong_credentials = UserLoginRequest(
        username_or_email="lockout_target",
        password="WrongPassword123!",
    )

    # 4 Failed attempts
    for _ in range(4):
        with pytest.raises(InvalidCredentials):
            await authentication_service.authenticate_user(
                db, tenant_id=tenant_id, credentials=wrong_credentials
            )

    # 5th attempt triggers lockout
    with pytest.raises(InvalidCredentials):
        await authentication_service.authenticate_user(
            db, tenant_id=tenant_id, credentials=wrong_credentials
        )

    # 6th attempt should raise AccountLocked
    with pytest.raises(AccountLocked):
        await authentication_service.authenticate_user(
            db, tenant_id=tenant_id, credentials=wrong_credentials
        )


@pytest.mark.asyncio
async def test_api_key_lifecycle_integration(db: AsyncSession):
    """Integration test: Create API Key -> Validate -> Deactivate."""
    tenant_id = uuid.uuid4()
    tenant = Tenant(id=tenant_id, name="API Key Tenant", code=f"t_{uuid.uuid4().hex[:6]}")
    db.add(tenant)
    await db.commit()

    user_in = UserCreate(
        username="apikey_user",
        email="apikey@lab.org",
        first_name="Key",
        last_name="Owner",
        password="ValidPassword123!",
        tenant_id=tenant_id,
    )
    user = await user_service.register_user(db, obj_in=user_in)

    api_key_obj, raw_key = await api_key_service.create_api_key(
        db, tenant_id=tenant_id, user_id=user.id, name="LIMS Ingest Key"
    )
    assert raw_key.startswith("eln_ak_")

    # Validate
    validated_key = await api_key_service.validate_api_key(db, raw_api_key=raw_key)
    assert validated_key.id == api_key_obj.id

    # Deactivate
    await api_key_service.revoke_api_key(db, id=api_key_obj.id, tenant_id=tenant_id)
