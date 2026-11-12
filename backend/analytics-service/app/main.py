from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import reports, categories, forecast

app = FastAPI(
    title="Analytics Service",
    version="1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router)
app.include_router(categories.router)
app.include_router(forecast.router)


@app.get("/")
def root():
    return {"message": "Analytics Service is running"}