import uvicorn
import os
import datetime
from fastapi import FastAPI, Request, Form, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

# Import local modules
from core.database import SessionLocal, engine
from core import auth, models, analytics

# Initialize Database
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Poultry AI-DBMS Pro")

# --- FIXED STATIC FILES LOGIC ---
base_dir = os.path.dirname(os.path.abspath(__file__))
static_dir = os.path.normpath(os.path.join(base_dir, "..", "frontend", "static"))

if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")
else:
    print(f"CRITICAL WARNING: {static_dir} not found.")

# Templates logic
template_dir = os.path.normpath(os.path.join(base_dir, "..", "frontend", "templates"))
templates = Jinja2Templates(directory=template_dir)

# --- DEPENDENCIES ---

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    email = auth.get_user_from_token(token)
    if not email:
        return None
    user = db.query(models.User).filter(models.User.email == email).first()
    return user

# --- AUTH ROUTES ---

@app.post("/register")
async def register_user(
    full_name: str = Form(...), 
    email: str = Form(...), 
    password: str = Form(...),
    farm_name: str = Form(...),
    country: str = Form(...),
    region: str = Form(...),
    city: str = Form(...),
    db: Session = Depends(get_db)
):
    try:
        existing_user = db.query(models.User).filter(models.User.email == email).first()
        if existing_user:
            return RedirectResponse(url="/auth?error=Email+already+registered", status_code=303)
        
        hashed_pw = auth.hash_password(password)
        new_user = models.User(
            full_name=full_name, 
            email=email, 
            hashed_password=hashed_pw, 
            farm_name=farm_name,
            country=country,
            region=region,
            city=city
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        access_token = auth.create_access_token(data={"sub": email})
        response = RedirectResponse(url="/dashboard", status_code=303)
        response.set_cookie(key="access_token", value=access_token, httponly=True)
        return response
    except Exception as e:
        db.rollback()
        return f"Error during registration: {str(e)}"

@app.post("/login")
async def login_user(
    email: str = Form(...), 
    password: str = Form(...), 
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.email == email).first()
    if not user or not auth.verify_password(password, user.hashed_password):
        return RedirectResponse(url="/auth?error=Invalid+credentials", status_code=303)  
    
    access_token = auth.create_access_token(data={"sub": user.email})
    response = RedirectResponse(url="/dashboard", status_code=303)
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/auth", status_code=303)
    response.delete_cookie("access_token")
    return response

@app.get("/auth", response_class=HTMLResponse)
async def auth_page(request: Request, user: models.User = Depends(get_current_user)):
    if user:
        return RedirectResponse(url="/dashboard")
    return templates.TemplateResponse("auth.html", {"request": request, "user": user})

# --- DASHBOARD & FUNCTIONAL ROUTES ---

@app.get("/", response_class=HTMLResponse)
async def homepage(request: Request, db: Session = Depends(get_db), user: models.User = Depends(get_current_user)):
    # Global dashboard: Aggregate data from ALL farmers
    logs = db.query(models.DailyLog).all()
    expenses = db.query(models.Expense).all()
    revenues = db.query(models.Revenue).all()
    vaccinations = db.query(models.Vaccination).all()
    
    # Process with all data to get industry-wide benchmarks
    insights = analytics.process_poultry_data(logs, expenses, revenues, vaccinations)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "logs": logs[:100], # Only show last 100 logs in table
        "insights": insights,
        "user": user,
        "is_global": True
    })

@app.get("/dashboard", response_class=HTMLResponse)
async def personalized_dashboard(
    request: Request, 
    flock_id: int = None,
    db: Session = Depends(get_db), 
    user: models.User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/auth")
    
    query = db.query(models.DailyLog)
    expense_query = db.query(models.Expense)
    revenue_query = db.query(models.Revenue)
    vaccination_query = db.query(models.Vaccination)
    
    user_flock_ids = [f.id for f in user.flocks]
    
    if flock_id:
        flock = db.query(models.Flock).filter(models.Flock.id == flock_id, models.Flock.user_id == user.id).first()
        if flock:
            query = query.filter(models.DailyLog.flock_id == flock_id)
            expense_query = expense_query.filter(models.Expense.flock_id == flock_id)
            revenue_query = revenue_query.filter(models.Revenue.flock_id == flock_id)
            vaccination_query = vaccination_query.filter(models.Vaccination.flock_id == flock_id)
        else:
            query = query.filter(models.DailyLog.flock_id.in_(user_flock_ids))
            flock_id = None
    else:
        query = query.filter(models.DailyLog.flock_id.in_(user_flock_ids))
        expense_query = expense_query.filter(models.Expense.flock_id.in_(user_flock_ids))
        revenue_query = revenue_query.filter(models.Revenue.flock_id.in_(user_flock_ids))
        vaccination_query = vaccination_query.filter(models.Vaccination.flock_id.in_(user_flock_ids))
    
    logs = query.order_by(models.DailyLog.log_date.desc()).limit(30).all()
    expenses = expense_query.all()
    revenues = revenue_query.all()
    vaccinations = vaccination_query.all()
    
    insights = analytics.process_poultry_data(logs, expenses, revenues, vaccinations)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request, 
        "logs": logs, 
        "insights": insights, 
        "user": user, 
        "is_global": False,
        "selected_flock_id": flock_id
    })

# --- NEW FUNCTIONAL ROUTES ---

@app.post("/add-expense")
async def add_expense(
    flock_id: int = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user: return RedirectResponse(url="/auth")
    new_exp = models.Expense(flock_id=flock_id, category=category, amount=amount, description=description)
    db.add(new_exp)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/add-revenue")
async def add_revenue(
    flock_id: int = Form(...),
    category: str = Form(...),
    amount: float = Form(...),
    description: str = Form(""),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user: return RedirectResponse(url="/auth")
    new_rev = models.Revenue(flock_id=flock_id, category=category, amount=amount, description=description)
    db.add(new_rev)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.post("/add-vaccination")
async def add_vaccination(
    flock_id: int = Form(...),
    vaccine_name: str = Form(...),
    scheduled_date: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user: return RedirectResponse(url="/auth")
    new_vac = models.Vaccination(
        flock_id=flock_id, 
        vaccine_name=vaccine_name, 
        scheduled_date=datetime.datetime.strptime(scheduled_date, "%Y-%m-%d").date()
    )
    db.add(new_vac)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/insights", response_class=HTMLResponse)
async def insights_page(
    request: Request,
    flock_id: int = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user: return RedirectResponse(url="/auth")
    
    # Logic similar to dashboard but specifically for deep AI insights
    user_flock_ids = [f.id for f in user.flocks]
    query = db.query(models.DailyLog)
    if flock_id:
        query = query.filter(models.DailyLog.flock_id == flock_id)
    else:
        query = query.filter(models.DailyLog.flock_id.in_(user_flock_ids))
    
    logs = query.order_by(models.DailyLog.log_date.desc()).all()
    expenses = db.query(models.Expense).filter(models.Expense.flock_id.in_(user_flock_ids)).all()
    revenues = db.query(models.Revenue).filter(models.Revenue.flock_id.in_(user_flock_ids)).all()
    vaccinations = db.query(models.Vaccination).filter(models.Vaccination.flock_id.in_(user_flock_ids)).all()
    
    insights = analytics.process_poultry_data(logs, expenses, revenues, vaccinations)
    
    return templates.TemplateResponse("insights.html", {
        "request": request,
        "insights": insights,
        "user": user,
        "selected_flock_id": flock_id
    })


@app.get("/records", response_class=HTMLResponse)
async def farm_records(
    request: Request,
    flock_id: int = None,
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/auth")
    
    query = db.query(models.DailyLog)
    user_flock_ids = [f.id for f in user.flocks]
    
    if flock_id:
        # Security check: verify flock ownership
        flock = db.query(models.Flock).filter(models.Flock.id == flock_id, models.Flock.user_id == user.id).first()
        if flock:
            query = query.filter(models.DailyLog.flock_id == flock_id)
        else:
            query = query.filter(models.DailyLog.flock_id.in_(user_flock_ids))
            flock_id = None
    else:
        query = query.filter(models.DailyLog.flock_id.in_(user_flock_ids))
    
    # Get all logs for records page, ordered by date
    logs = query.order_by(models.DailyLog.log_date.desc()).all()
    
    return templates.TemplateResponse("records.html", {
        "request": request,
        "logs": logs,
        "user": user,
        "selected_flock_id": flock_id
    })

@app.post("/add-flock")
async def add_flock(
    name: str = Form(...),
    breed: str = Form(...),
    initial_count: int = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/auth", status_code=303)
    
    new_flock = models.Flock(name=name, breed=breed, initial_count=initial_count, user_id=user.id)
    db.add(new_flock)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

@app.get("/entry", response_class=HTMLResponse)
async def entry_page(request: Request, flock_id: int = None, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/auth")
    return templates.TemplateResponse("data_entry.html", {
        "request": request, 
        "user": user,
        "selected_flock_id": flock_id
    })

@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, user: models.User = Depends(get_current_user)):
    if not user:
        return RedirectResponse(url="/auth")
    return templates.TemplateResponse("settings.html", {"request": request, "user": user})

@app.post("/update-profile")
async def update_profile(
    full_name: str = Form(...),
    farm_name: str = Form(...),
    country: str = Form(...),
    region: str = Form(...),
    city: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/auth")
    
    user.full_name = full_name
    user.farm_name = farm_name
    user.country = country
    user.region = region
    user.city = city
    
    db.commit()
    return RedirectResponse(url="/settings?success=Profile+updated", status_code=303)

@app.post("/save-log")
async def save_log(
    flock_id: int = Form(...),
    log_date: str = Form(...),
    feed: float = Form(...),
    water: float = Form(...),
    weight: float = Form(...),
    mortality: int = Form(...),
    eggs: int = Form(0),
    db: Session = Depends(get_db),
    user: models.User = Depends(get_current_user)
):
    if not user:
        return RedirectResponse(url="/auth")
    
    flock = db.query(models.Flock).filter(models.Flock.id == flock_id, models.Flock.user_id == user.id).first()
    if not flock:
        return "Access Denied: You do not own this flock."

    new_log = models.DailyLog(
        flock_id=flock_id, log_date=log_date, feed_consumed_kg=feed,
        water_consumed_liters=water, avg_bird_weight_g=weight,
        mortality_count=mortality, eggs_collected=eggs
    )
    db.add(new_log)
    db.commit()
    return RedirectResponse(url="/dashboard", status_code=303)

if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)