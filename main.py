from bson import ObjectId
from fastapi import FastAPI, HTTPException, Header, Depends
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from pymongo import MongoClient
from jose import jwt, JWTError
from passlib.context import CryptContext

SECRET_KEY = "amfMuAl3WczKR4IswrvpqFcAVot1k776"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hashPass(password: str):
    return pwd_context.hash(password)

def verifyPass(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def genAccessToken(data: dict, expires_delta: timedelta = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def verAccessToken(token: str):
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])


def getUser(token: str = Header(..., alias="Authorization")):
    if not token.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = token.split(" ")[1]
    try:
        payload = verAccessToken(token)
        return payload["sub"]
    except JWTError:
        raise HTTPException(status_code=403, detail="Invalid or expired token")

app = FastAPI(
    title = "Doctor Profile API",
    version = "1.0"
)

client = MongoClient("localhost",27017)
db = client["starcoach-db"]
doctors_collection = db["doctors"]
users_collection = db["users"]
appointments_collection = db["appointments"]

class Credentials(BaseModel):
    email: str
    password: str

class Slot(BaseModel):
    date: str
    day: str
    slots: List[str]

class Doctor(BaseModel):
    name: str
    specialty: str
    available_slots: List[Slot]

class Appointment(BaseModel):
    doctor_id: str
    date: str
    time_slot: str


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

@app.post("/api/v1/auth/signup")
def signup(creds: Credentials):
    if users_collection.find_one({"email": creds.email}):
        raise HTTPException(status_code=400, detail="User already exists")
    
    if len(creds.password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    

    hashed_password = hashPass(creds.password)
    user = {
        "email": creds.email,
        "hashed_password": hashed_password,
        "created_at": datetime.utcnow().isoformat()
    }

    result = users_collection.insert_one(user)
    return {
        "success": True,
        "message": "User registered successfully.",
        "user_id": str(result.inserted_id)
    }

@app.post("/api/v1/auth/signin")
def signin(creds: Credentials):
    user = users_collection.find_one({"email": creds.email})
    if not user or not verifyPass(creds.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = genAccessToken({"sub": creds.email})
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/api/v1/appointments")
def list_appointments() :
    appointments = list(appointments_collection.find())
    for appt in appointments:
        appt["_id"] = str(appt["_id"])
    return {"success": True, "appointments": appointments}
    
@app.post("/api/v1/appointments")
def create_appointment(appointment: Appointment):
    app = {
        #"user_id": users_collection.find_one({"email": creds.email})
        "doctor_id": appointment.doctor_id,
        "date": appointment.date,
        "time_slot": appointment.time_slot,
        "status": "booked",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = appointments_collection.insert_one(app)

    return {
        "success": True,
        "message": "Appointment booked successfully.",
        "appointment_id": str(result.inserted_id)
    }

@app.put("/api/v1/appointments/{appointment_id}")
def get_appointment(appointment_id: str, new_appointment: Appointment):
    if not isValidObjectId(appointment_id):
        raise HTTPException(status_code=400, detail="Invalid appointment ID format")
    
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    isR = appointments_collection.delete_one({"_id": ObjectId(appointment_id)})

    if not isR:
        return {
            "success": False,
            "message": "Failed to modify appointments"
        }
    
    app = {
        #"user_id": users_collection.find_one({"email": creds.email})
        "doctor_id": new_appointment.doctor_id,
        "date": new_appointment.date,
        "time_slot": new_appointment.time_slot,
        "status": "booked",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }

    result = appointments_collection.insert_one(app)

    return {
        "success": True,
        "message": "Appointment booked successfully.",
        "appointment_id": str(result.inserted_id)
    }

    


@app.delete("/api/v1/appointments/{appointment_id}")
def delete_appointment(appointment_id: str):
    if not isValidObjectId(appointment_id):
        raise HTTPException(status_code=400, detail="Invalid appointment ID format")
    
    appointment = appointments_collection.find_one({"_id": ObjectId(appointment_id)})

    if not appointment:
        raise HTTPException(status_code=404, detail="Appointment not found")
    
    if appointments_collection.delete_one({"_id": ObjectId(appointment_id)}):
        return {
            "success": True,
            "message": "Appointment removed successfully.",
        }
    else:
        return {
            "success": False,
            "message": "Failed to remove appointment from database.",
        }

@app.get("/")
def root():
    return {"message": "Welcome to the Doctor Profile API!"}
