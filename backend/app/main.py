from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from .services.catalogue import CatalogueService

app = FastAPI(title="Peblo TV Mini API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
service = CatalogueService()

class ShowIn(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    synopsis: str = Field(default="", max_length=2000)
    section: str = Field(min_length=1)
    category: str = Field(min_length=1)
    status: str = "draft"

class Show(ShowIn):
    id: int
    languages: list[str] = []

class User(BaseModel):
    email: str
    role: str

def current_user(x_user: str = Header(default="admin@example.com")) -> User:
    users = {"admin@example.com": User(email="admin@example.com", role="admin"), "editor@example.com": User(email="editor@example.com", role="editor")}
    if x_user not in users:
        raise HTTPException(401, "Unknown demo user. Use X-User: admin@example.com or editor@example.com")
    return users[x_user]

def admin_only(user: User = Depends(current_user)) -> User:
    if user.role != "admin":
        raise HTTPException(403, "Only admins can publish the catalogue")
    return user

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/admin/shows", response_model=list[Show])
def shows(_: User = Depends(current_user)):
    return service.shows

@app.post("/admin/shows", response_model=Show, status_code=201)
def create_show(payload: ShowIn, _: User = Depends(current_user)):
    return service.create_show(payload.model_dump())

@app.get("/admin/validation-report")
def validation(_: User = Depends(current_user)):
    return service.validation_report()

@app.post("/admin/catalog/publish")
def publish(user: User = Depends(admin_only)):
    try:
        return service.publish(user.email)
    except ValueError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

@app.get("/admin/catalog/publish-runs")
def publish_runs(_: User = Depends(current_user)):
    return service.publish_runs

@app.get("/catalog")
def catalog():
    return service.read_catalogue()

@app.get("/catalog/search")
def search(q: str = Query(default=""), category: str | None = None, language: str | None = None, section: str | None = None):
    return service.search(q, category, language, section)
