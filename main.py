from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel # <--- 1. Add this import
from db import supabase
import uuid
import mimetypes
import os # <--- 2. Add this import to read .env
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# -------------------------------------------------
# CORS
# -------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------
# ADMIN LOGIN LOGIC
# -------------------------------------------------

# 3. Create the data model for the login request
class AdminLogin(BaseModel):
    username: str
    password: str

# 4. Create the login endpoint
@app.post("/admin/login")
async def admin_login(data: AdminLogin):
    # Fetch values from your .env file
    stored_username = os.getenv("ADMIN_USERNAME")
    stored_password = os.getenv("ADMIN_PASSWORD")

    # Verify credentials
    if data.username == stored_username and data.password == stored_password:
        return {"status": "success", "message": "Access Granted"}
    else:
        # 401 means "Unauthorized"
        raise HTTPException(status_code=401, detail="Invalid ID or Password")
    
    # 1. Define the model for awarding a winner
class WinnerAssignment(BaseModel):
    entry_id: str
    winner_rank: str

# 2. Create the route to update the entry in Supabase
@app.post("/admin/assign-winner")
async def assign_winner(data: WinnerAssignment):
    try:
        # Update the specific entry in Supabase using .update() and .eq() filter
        response = (
            supabase.table("competition_entries")
            .update({"winner_rank": data.winner_rank}) # The new column you added
            .eq("id", data.entry_id)                   # Target specific row
            .execute()
        )
        
        # Check if the update was successful
        if not response.data:
            raise HTTPException(status_code=404, detail="Entry not found")
            
        return {"status": "success", "message": f"Awarded {data.winner_rank} successfully"}
        
    except Exception as e:
        print(f"Error updating winner: {e}")
        raise HTTPException(status_code=500, detail="Database update failed")

# -------------------------------------------------
# TEST ROUTE
# -------------------------------------------------
@app.get("/")
def root():
    return {"status": "backend working"}

# -------------------------------------------------
# SUBMIT ENTRY
# -------------------------------------------------
# ... existing imports and setup ...

@app.post("/submit-entry")
async def submit_entry(
    competition_type: str = Form(...),
    full_name: str = Form(...),
    organization: str = Form(None),
    address: str = Form(...),
    city: str = Form(...),
    contact: str = Form(...),
    email: str = Form(...),
    description: str = Form(None),
    photos: list[UploadFile] = File(...)
):
    # 1️⃣ Insert participant entry
    entry = (
        supabase
        .table("competition_entries")  # matches Supabase table name with underscore
        .insert(
            {
                "competition_type": competition_type,
                "full_name": full_name,
                "organization": organization,
                "address": address,
                "city": city,
                "contact": contact,
                "email": email,
                "description": description,
            }
        )
        .execute()
    )

    entry_id = entry.data[0]["id"]

    # 2️⃣ Upload images
    for photo in photos:
        # Skip empty uploads
        if not photo.filename:
            continue

        # Validate and normalize MIME type (only allow JPEG/PNG)
        guessed_type, _ = mimetypes.guess_type(photo.filename)
        mime_type = guessed_type or photo.content_type or "application/octet-stream"

        if mime_type not in {"image/jpeg", "image/png"}:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported image type for file '{photo.filename}'. Please upload JPG or PNG images only.",
            )

        file_bytes = await photo.read()

        filename = f"{uuid.uuid4()}_{photo.filename}"
        file_path = f"{competition_type}/{entry_id}/{filename}"

        supabase.storage.from_("competition-uploads").upload(
            file_path,
            file_bytes,
            {"content-type": mime_type},
        )

        # For supabase-py, get_public_url returns a string URL directly
        public_url = (
            supabase.storage.from_("competition-uploads").get_public_url(file_path)
        )

        supabase.table("entry_images").insert(
            {
                "entry_id": entry_id,
                "image_url": public_url,
            }
        ).execute()

    return {"status": "success", "entry_id": entry_id}

# ... keep admin/entries, but update table names there too ...
@app.get("/admin/entries")
def get_entries():
    entries = (
        supabase.table("competition_entries")
        .select("*")
        .order("created_at", desc=True)
        .execute()
        .data
    )

    for entry in entries:
        images = (
            supabase.table("entry_images")
            .select("image_url")
            .eq("entry_id", entry["id"])
            .execute()
            .data
        )
        entry["images"] = images

    return entries
