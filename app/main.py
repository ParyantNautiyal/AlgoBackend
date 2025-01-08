from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from app.routers import kite, orders, instruments
from app.database import get_db
from sqlalchemy import text

app = FastAPI(title="Trading API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routers
app.include_router(kite.router)
app.include_router(orders.router)
app.include_router(instruments.router)

@app.get("/")
async def root():
    return {"message": "Welcome to your Trading API!"}

@app.get("/test-db")
async def test_db():
    try:
        with get_db() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            return {"message": "Database connection successful!", "result": result}
    except Exception as e:
        return {"error": f"Database connection failed: {str(e)}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True) 