# gateway/main.py

from fastapi import FastAPI, HTTPException, Request, Depends, status
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
import httpx
import time
import logging
from typing import Any
from datetime import timedelta
from auth import verify_token, create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES

# Set up logging for Activity 3
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="API Gateway", version="1.0.0")

# Service URLs - Added course service for Activity 1
SERVICES = {
    "student": "http://localhost:8001",
    "course": "http://localhost:8002"
}

# Activity 3: Add Request Logging
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    # Process the request
    response = await call_next(request)
    
    process_time = time.time() - start_time
    logger.info(
        f"Method: {request.method} Path: {request.url.path} "
        f"Status: {response.status_code} Process Time: {process_time:.4f}s"
    )
    return response

# Activity 4: Error Handling
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global Error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "details": str(exc)},
    )

@app.exception_handler(httpx.RequestError)
async def httpx_exception_handler(request: Request, exc: httpx.RequestError):
    return JSONResponse(
        status_code=503,
        content={"message": "Service Unavailable", "details": f"Failed to connect to backend service: {str(exc)}"},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"message": "Error", "details": exc.detail},
    )

async def forward_request(service: str, path: str, method: str, **kwargs) -> Any:
    """Forward request to the appropriate microservice"""
    if service not in SERVICES:
        raise HTTPException(status_code=404, detail="Service not found")        

    url = f"{SERVICES[service]}{path}"

    async with httpx.AsyncClient() as client:
        if method == "GET":
            response = await client.get(url, **kwargs)
        elif method == "POST":
            response = await client.post(url, **kwargs)
        elif method == "PUT":
            response = await client.put(url, **kwargs)
        elif method == "DELETE":
            response = await client.delete(url, **kwargs)
        else:
            raise HTTPException(status_code=405, detail="Method not allowed")
            
        # Check if the backend service returned an error status code
        if response.status_code >= 400:
            error_detail = response.text
            try:
                error_detail = response.json()
            except:
                pass
            raise HTTPException(status_code=response.status_code, detail=error_detail)
            
        return JSONResponse(
            content=response.json() if response.text else None,
            status_code=response.status_code
        )

# Activity 2: Authentication Token Endpoint
@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    # In a real application, you would verify the credentials against a database
    if form_data.username == "admin" and form_data.password == "admin123":
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": form_data.username}, expires_delta=access_token_expires
        )
        return {"access_token": access_token, "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@app.get("/")
def read_root():
    return {"message": "API Gateway is running", "available_services": list(SERVICES.keys())}


# --- Student Service Routes (Protected) ---
@app.get("/gateway/students", dependencies=[Depends(verify_token)])
async def get_all_students():
    """Get all students through gateway"""
    return await forward_request("student", "/api/students", "GET")

@app.get("/gateway/students/{student_id}", dependencies=[Depends(verify_token)])
async def get_student(student_id: int):
    """Get a student by ID through gateway"""
    return await forward_request("student", f"/api/students/{student_id}", "GET")

@app.post("/gateway/students", dependencies=[Depends(verify_token)])
async def create_student(request: Request):
    """Create a new student through gateway"""
    body = await request.json()
    return await forward_request("student", "/api/students", "POST", json=body) 

@app.put("/gateway/students/{student_id}", dependencies=[Depends(verify_token)])
async def update_student(student_id: int, request: Request):
    """Update a student through gateway"""
    body = await request.json()
    return await forward_request("student", f"/api/students/{student_id}", "PUT", json=body)

@app.delete("/gateway/students/{student_id}", dependencies=[Depends(verify_token)])
async def delete_student(student_id: int):
    """Delete a student through gateway"""
    return await forward_request("student", f"/api/students/{student_id}", "DELETE")

# --- Course Service Routes (Protected) ---
@app.get("/gateway/courses", dependencies=[Depends(verify_token)])
async def get_all_courses():
    """Get all courses through gateway"""
    return await forward_request("course", "/api/courses", "GET")

@app.get("/gateway/courses/{course_id}", dependencies=[Depends(verify_token)])
async def get_course(course_id: int):
    """Get a course by ID through gateway"""
    return await forward_request("course", f"/api/courses/{course_id}", "GET")

@app.post("/gateway/courses", dependencies=[Depends(verify_token)])
async def create_course(request: Request):
    """Create a new course through gateway"""
    body = await request.json()
    return await forward_request("course", "/api/courses", "POST", json=body) 

@app.put("/gateway/courses/{course_id}", dependencies=[Depends(verify_token)])
async def update_course(course_id: int, request: Request):
    """Update a course through gateway"""
    body = await request.json()
    return await forward_request("course", f"/api/courses/{course_id}", "PUT", json=body)

@app.delete("/gateway/courses/{course_id}", dependencies=[Depends(verify_token)])
async def delete_course(course_id: int):
    """Delete a course through gateway"""
    return await forward_request("course", f"/api/courses/{course_id}", "DELETE")
