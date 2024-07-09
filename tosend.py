import serial
import requests
from datetime import datetime, timedelta

# Replace with the correct serial port of your RFID reader
SERIAL_PORT = 'COM3'  # Example for Windows, replace with your actual port

# Firebase Realtime Database URL
FIREBASE_URL = 'https://rfid-6f2af-default-rtdb.firebaseio.com/'

# Dictionary to keep track of the last read timestamps for each RFID
last_read_times = {}

# Function to handle RFID scan and send data to Firebase
def handle_rfid_scan(rfid_uid):
    # Trim RFID UID to remove extra spaces or newline characters
    rfid_uid = rfid_uid.strip()
    
    # Get student name from Firebase
    firebase_path = f'rfid_mapping/{rfid_uid}'
    firebase_response = requests.get(f'{FIREBASE_URL}{firebase_path}.json')
    
    if firebase_response.status_code == 200:
        student_data = firebase_response.json()
        if student_data:
            student_name = student_data['studentName']
        else:
            print(f'RFID UID {rfid_uid} not found in the mapping.')
            return
    else:
        print(f'Failed to retrieve student name for RFID: {rfid_uid}')
        return

    # Get the current timestamp
    now = datetime.now()

    # Check if this RFID was read within the last 45 minutes
    if rfid_uid in last_read_times:
        last_read_time = last_read_times[rfid_uid]
        if now - last_read_time < timedelta(minutes=45):  # 45-minute debounce window
            print(f'Debounced multiple reads for RFID UID: {rfid_uid}')
            return
    
    # Update the last read time for this RFID
    last_read_times[rfid_uid] = now

    timestamp_str = now.strftime('%m/%d/%Y %I:%M:%S %p')  # Format as MM/DD/YYYY HH:MM:SS AM/PM

    # Construct Firebase database path and payload
    firebase_data = {
        'studentName': student_name,
        'timestamp': timestamp_str
    }

    # Send POST request to Firebase
    firebase_response = requests.post(f'{FIREBASE_URL}attendance.json', json=firebase_data)
    
    if firebase_response.status_code == 200:
        print(f'Successfully logged attendance for RFID: {rfid_uid}')
        print(f'Student Name: {student_name}')
        print(f'Timestamp: {timestamp_str}')
    else:
        print(f'Failed to log attendance for RFID: {rfid_uid}')

# Main function to listen for RFID scans
def main():
    with serial.Serial(SERIAL_PORT, 9600, timeout=1) as ser:
        while True:
            line = ser.readline().decode('utf-8').strip()
            # Extract the UID from the line
            if "Card UID:" in line:
                rfid_uid = line.split("Card UID:")[1].strip()
                handle_rfid_scan(rfid_uid)

if __name__ == '__main__':
    main()
