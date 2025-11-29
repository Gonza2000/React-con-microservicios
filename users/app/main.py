from fastapi import FastAPI, HTTPException
from sqlmodel import SQLModel, Field, create_engine, Session, select
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional


sqlite_file_name = "users.db"
sqlite_url = f"sqlite:///{sqlite_file_name}"
engine = create_engine(sqlite_url, echo=True)

class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str
    password: str

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()


class UserLogin(BaseModel):
    username: str
    password: str

@app.post("/register")
def register(user: UserLogin):
    with Session(engine) as session:
        existing_user = session.exec(select(User).where(User.username == user.username)).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="Username already exists")
        new_user = User(username=user.username, password=user.password)
        session.add(new_user)
        session.commit()
        return {"message": "User registered successfully"}

@app.post("/login")
def login(user: UserLogin):
    with Session(engine) as session:
        statement = select(User).where(User.username == user.username).where(User.password == user.password)
        result = session.exec(statement).first()
        if not result:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return {"message": "Login successful", "user_id": result.id}

@app.get("/users")
def get_users():
    with Session(engine) as session:
        users = session.exec(select(User)).all()
        return [{"id": u.id, "username": u.username} for u in users]
