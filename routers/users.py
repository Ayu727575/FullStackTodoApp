import sys

sys.path.append("..")

from starlette import status
from starlette.responses import RedirectResponse
from fastapi import Depends, APIRouter, Request, Form
import models
from database import engine, SessionLocal
from sqlalchemy.orm import Session
from .auth import get_current_user, verify_password, get_password_hash

from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter(
    prefix="/users",
    tags=["users"],
    responses={404: {"description": "Not found"}}
)

models.Base.metadata.create_all(bind=engine)
templates = Jinja2Templates(directory="templates")


def get_db():
    try:
        db = SessionLocal()
        yield db
    finally:
        db.close()


@router.get("/edit-password", response_class=HTMLResponse)
async def change_password(request: Request):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    return templates.TemplateResponse("edit-password.html", {"request": request, "user": user})


@router.post("/edit-password", response_class=HTMLResponse)
async def update_password(request: Request, username: str = Form(...), password: str = Form(...),
                          new_password: str = Form(...), db: Session = Depends(get_db)):
    user = await get_current_user(request)
    if user is None:
        return RedirectResponse(url="/auth", status_code=status.HTTP_302_FOUND)
    user_data = db.query(models.Users).filter(models.Users.username == user.get("username")).first()
    msg = "Invalid username or password"
    if user_data is not None:
        if user_data.username == username and verify_password(password, user_data.hashed_password):
            updated_password = get_password_hash(new_password)
            user_data.hashed_password = updated_password
            db.add(user_data)
            db.commit()
            msg = "Password updated"
    return templates.TemplateResponse("edit-password.html",
                                      {"request": request, "user": user, "msg": msg})
