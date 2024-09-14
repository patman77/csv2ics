import pandas as pd
from ics import Calendar, Event
from datetime import datetime, timedelta
import sys

# Check if a file path was passed as a command-line argument
if len(sys.argv) != 2:
    print("Usage: python script.py <csv_file>")
    sys.exit(1)

# Get the CSV file from command-line argument
csv_file = sys.argv[1]

# Load the CSV file
df = pd.read_csv(csv_file)

# Initialize a new calendar
calendar = Calendar()


# Helper function to convert date strings to datetime
def convert_to_datetime(date_str, base_date=None):
    # Check if the string contains a full date or just time
    if len(date_str.split()) > 2:
        return datetime.strptime(date_str, "%A %d.%m.%Y %I:%M %p")
    else:
        # If only time is provided, merge it with the base date
        return datetime.strptime(
            base_date.strftime("%A %d.%m.%Y") + " " + date_str, "%A %d.%m.%Y %I:%M %p"
        )


# Convert the timetable to calendar events
for _, row in df.iterrows():
    event = Event()
    event.name = row["Task"]

    start_time_str = row["Day & Time"].split(" - ")[0].strip()
    end_time_str = row["Day & Time"].split(" - ")[1].strip()

    # Get start time with full date
    start_time = convert_to_datetime(start_time_str)

    # Get end time, assuming only the time part might be given
    end_time = convert_to_datetime(end_time_str, base_date=start_time)

    # Check if the end time is earlier than the start time and adjust
    if end_time <= start_time:
        end_time += timedelta(days=1)  # Add one day to the end time if necessary

    event.begin = start_time
    event.end = end_time
    event.description = row["Details"]

    calendar.events.add(event)

# Save the calendar to an .ics file
ics_file_path = "frontend_interview_preparation_timetable.ics"
with open(ics_file_path, "w") as ics_file:
    ics_file.writelines(calendar)

print(f"ICS file saved to {ics_file_path}")
