from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import pandas as pd
from ics import Calendar, Event
from datetime import datetime, timedelta
from pathlib import Path
import os

# Initialize FastAPI app
app = FastAPI()

# Mount static files (for CSS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates setup for rendering HTML
templates = Jinja2Templates(directory="templates")

# Directory for storing uploads
upload_dir = Path("uploads")
upload_dir.mkdir(exist_ok=True)


# Upload page
@app.get("/", response_class=HTMLResponse)
async def upload_form():
    return templates.TemplateResponse("index.html", {"request": {}})


# Handle file upload and conversion to ICS
@app.post("/upload/")
async def handle_upload(file: UploadFile = File(...)):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Invalid file format. Please upload a CSV file."
        )

    try:
        # Save uploaded file to the server
        file_location = upload_dir / file.filename
        with open(file_location, "wb") as f:
            f.write(file.file.read())

        # Convert CSV to ICS
        ics_file_path = convert_csv_to_ics(file_location)

        # Ensure file exists before serving it
        if os.path.exists(ics_file_path):
            return FileResponse(
                ics_file_path,
                media_type="application/octet-stream",
                filename=ics_file_path.name,
            )
        else:
            raise HTTPException(status_code=500, detail="Could not generate ICS file.")

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")


def convert_csv_to_ics(csv_path: Path):
    try:
        # Read the CSV
        df = pd.read_csv(csv_path)

        calendar = Calendar()

        # Assuming the CSV has columns 'Task', 'Day & Time', 'Details'
        for _, row in df.iterrows():
            event = Event()
            event.name = row["Task"]

            start_time_str = row["Day & Time"].split(" - ")[0].strip()
            end_time_str = row["Day & Time"].split(" - ")[1].strip()

            # Parse start time
            start_time = datetime.strptime(start_time_str, "%A %d.%m.%Y %I:%M %p")

            # Check if end time contains only time and merge with start date
            try:
                end_time = datetime.strptime(end_time_str, "%A %d.%m.%Y %I:%M %p")
            except ValueError:
                # If only time is given, merge it with the start date
                end_time = datetime.strptime(
                    f"{start_time.strftime('%A %d.%m.%Y')} {end_time_str}",
                    "%A %d.%m.%Y %I:%M %p",
                )

            # Handle overnight events
            if end_time <= start_time:
                end_time += timedelta(days=1)

            event.begin = start_time
            event.end = end_time
            event.description = row["Details"]

            calendar.events.add(event)

        # Save as .ics file
        ics_file_path = upload_dir / (csv_path.stem + ".ics")
        with open(ics_file_path, "w") as f:
            f.writelines(calendar)

        return ics_file_path

    except Exception as e:
        raise ValueError(f"Error converting CSV to ICS: {str(e)}")
