import asyncio
import sys
from app.db.session import async_session_maker
from app.services.identity.authentication_service import authentication_service
from app.schemas.identity import UserLoginRequest
from app.crud.crud_tenant import tenant as crud_tenant

async def main():
    async with async_session_maker() as db:
        tenants = await crud_tenant.get_multi(db, limit=1)
        current_tenant = tenants[0]
        login_in = UserLoginRequest(username_or_email="login_test@example.com", password="SecurePassword123!")
        
        try:
            user, session_token, refresh_token = await authentication_service.authenticate_user(
                db,
                tenant_id=current_tenant.id,
                credentials=login_in
            )
            print("Success")
        except Exception as e:
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
