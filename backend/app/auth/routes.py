from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.auth.jwt_handler import create_access_token, decode_access_token, hash_password, verify_password
from app.auth.models import Role, TokenResponse, UserCreate, UserLogin, UserPublic
from app.db.mongo_client import get_db

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> UserPublic:
    try:
        payload = decode_access_token(credentials.credentials)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)) from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    db = get_db()
    doc = await db.users.find_one({"_id": user_id})
    if not doc:
        # Also try ObjectId-style lookup via string id field
        doc = await db.users.find_one({"id": user_id})
    if not doc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    return UserPublic(
        id=str(doc.get("_id", doc.get("id"))),
        email=doc["email"],
        name=doc["name"],
        role=Role(doc["role"]),
    )


def require_role(*roles: Role):
    async def _checker(user: UserPublic = Depends(get_current_user)) -> UserPublic:
        if user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient role")
        return user

    return _checker


@router.post("/signup", response_model=TokenResponse)
async def signup(body: UserCreate):
    db = get_db()
    existing = await db.users.find_one({"email": body.email.lower()})
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

    from uuid import uuid4

    user_id = str(uuid4())
    doc = {
        "_id": user_id,
        "email": body.email.lower(),
        "name": body.name,
        "role": body.role.value,
        "password_hash": hash_password(body.password),
        "created_at": datetime.now(timezone.utc),
        "teacher_id": None,
    }
    await db.users.insert_one(doc)

    token = create_access_token(
        user_id,
        {"role": body.role.value, "email": doc["email"], "name": body.name},
    )
    user = UserPublic(id=user_id, email=doc["email"], name=body.name, role=body.role)
    return TokenResponse(access_token=token, user=user)


@router.post("/login", response_model=TokenResponse)
async def login(body: UserLogin):
    db = get_db()
    doc = await db.users.find_one({"email": body.email.lower()})
    if not doc or not verify_password(body.password, doc["password_hash"]):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    if doc["role"] != body.role.value:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Account is registered as {doc['role']}, not {body.role.value}",
        )

    token = create_access_token(
        str(doc["_id"]),
        {"role": doc["role"], "email": doc["email"], "name": doc["name"]},
    )
    user = UserPublic(
        id=str(doc["_id"]),
        email=doc["email"],
        name=doc["name"],
        role=Role(doc["role"]),
    )
    return TokenResponse(access_token=token, user=user)


@router.get("/me", response_model=UserPublic)
async def me(user: UserPublic = Depends(get_current_user)):
    return user
