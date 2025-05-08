from bson import ObjectId
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from pymongo import MongoClient
from jose import jwt

app = FastAPI(
    title = "Doctor Profile API",
    version = "1.0"
)

client = MongoClient("localhost",27017)
db = client["starcoach-db"]
doctors_collection = db["doctors"]

class Slot(BaseModel):
    date: str
    day: str
    slots: List[str]

class Doctor(BaseModel):
    name: str
    specialty: str
    available_slots: List[Slot]

def isValidObjectId(object_id: str) -> bool:
    try:
        ObjectId(object_id)
        return True
    except Exception:
        return False
    
@app.post("/api/v1/doctors/")
def create_doctor(doctor: Doctor):
    slots_dict = {s.date : s.slots for s in doctor.available_slots}
    
    doc = {
        "name": doctor.name,
        "specialty": doctor.specialty,
        "available_slots": slots_dict,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = doctors_collection.insert_one(doc)
    
    return {
        "success": True,
        "message": "Doctor profile created successfully.",
        "doctor_id": str(result.inserted_id)
    }

@app.get("/api/v1/doctors/{doctor_id}")
def get_doctor(doctor_id: str):
    if not isValidObjectId(doctor_id):
        raise HTTPException(status_code=400, detail="Invalid doctor ID format")
    
    doctor = doctors_collection.find_one({"_id": ObjectId(doctor_id)})

    if not doctor:
        raise HTTPException(status_code=404, detail="Doctor not found")
    
    slots_list = []
    for date, slots in doctor["available_slots"].items():
        day = datetime.strptime(date, "%Y-%m-%d").strftime("%A")
        slots_list.append({"date": date, "day": day, "slots": slots})
    
    return {
        "success": True,
        "doctor": {
            "id": str(doctor["_id"]),
            "name": doctor["name"],
            "specialty": doctor["specialty"],
            "available_slots": slots_list
        }
    }

@app.get("/")
def root():
    return {"message": "Welcome to the Doctor Profile API!"}
