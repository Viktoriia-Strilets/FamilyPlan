from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware

from app.database import Base, engine, SessionLocal
from app.core.config import SESSION_SECRET_KEY
from app.core.security import get_password_hash
from app.models import UserModel
from app.routers import auth, users, families, admin, oauth


def seed_super_admin():
    db = SessionLocal()
    try:
        from app.core.config import ADMIN_EMAIL, ADMIN_USERNAME, ADMIN_PASSWORD

        existing_admin = (
            db.query(UserModel)
            .filter(UserModel.email == ADMIN_EMAIL)
            .first()
        )
        if not existing_admin:
            db.add(UserModel(
                username=ADMIN_USERNAME,
                email=ADMIN_EMAIL,
                password_hash=get_password_hash(ADMIN_PASSWORD),
                role="admin",
                family_id=None,
            ))
            db.commit()
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    seed_super_admin()
    yield


app = FastAPI(title="User Service", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET_KEY,
    same_site="lax",
    https_only=False,
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(families.router)
app.include_router(admin.router)
app.include_router(oauth.router)


@app.get("/")
def root():
    return {"message": "User Service is running"}
