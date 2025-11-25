from fastapi import FastAPI, HTTPException, Request, BackgroundTasks
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from quiz_solver import QuizSolver
import logging

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load credentials from environment variables
YOUR_EMAIL = os.getenv("STUDENT_EMAIL", "your-email@example.com")
YOUR_SECRET = os.getenv("STUDENT_SECRET", "your-secret-string")

class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str

@app.post("/solve")
async def solve_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint to receive and solve quiz tasks
    """
    try:
        # Verify secret
        if request.secret != YOUR_SECRET:
            raise HTTPException(status_code=403, detail="Invalid secret")
        
        # Verify email
        if request.email != YOUR_EMAIL:
            raise HTTPException(status_code=403, detail="Invalid email")
        
        logger.info(f"Received quiz request for URL: {request.url}")
        
        # Initialize quiz solver
        solver = QuizSolver(
            email=request.email,
            secret=request.secret
        )
        
        # Add quiz solving to background tasks
        background_tasks.add_task(solver.solve_quiz_chain, request.url)
        
        return JSONResponse(
            status_code=200,
            content={
                "status": "success",
                "message": "Quiz processing started in background"
            }
        )
    
    except HTTPException as e:
        raise e
    except Exception as e:
        logger.error(f"Error processing quiz: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)}
    )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=400,
        content={"detail": "Invalid request body", "errors": exc.errors()}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)