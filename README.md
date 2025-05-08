# Simple Doctor API
This is a Simple API written with FastAPI for managing doctors, customers and appointments


## API Details:

This API uses HTTP protocol for creating and fetching profile through the following method :

- **Method**: `POST`, `GET`
- **Endpoint**: `/api/v1/doctors/`

### Request Body:
```json
  {
    "name": "Dr. John Smith",
    "specialty": "Cardiology",
    "available_slots": [
        {
            "date": "2025-02-15",
            "day": "Monday",
            "slots": ["09:00-11:00", "14:00-16:00"]
        },
        {
            "date": "2025-02-17",
            "day": "Wednesday",
            "slots": ["10:00-12:00"]
        }
    ]
}
```

### Response:
- Success:
```json
{
    "success": true,
    "message": "Doctor profile created successfully.",
    "doctor_id": 1
}
```

- Error:
```json
{
    "success": false,
    "message": "Invalid user ID or missing data."
}
```

## Database Structure for Doctors API

The database is designed to store and manage doctor profiles and related data.

It uses MongoDB via pymongo to save the doctors' information in the following format:

#### **Schema**
```json
{
  "_id": ObjectId("..."),           // Automatically generated unique doctor ID
  "user_id": ObjectId("..."),       // Reference to the user document (foreign key equivalent)
  "name": "Dr. Jane Doe",           // Full name of the doctor
  "specialty": "Cardiology",        // Doctor's specialty
  "available_slots": {
    "2025-05-01": ["09:00", "10:00", "11:00"],
    "2025-05-02": ["14:00", "15:00"]
  },
  "created_at": ISODate("2025-05-01T08:00:00Z"),   // Creation timestamp
  "updated_at": ISODate("2025-05-01T08:00:00Z")    // Last update timestamp
}

```


## How to Run

To run this FastAPI Code, you need to install python and uvicorn (Solution for HTTP Server) through pip.

```shell
pip install uvicorn
```

And then run the code with uvicorn:

```shell
uvicorn main:app
```