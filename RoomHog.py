import json
import os

import gspread
from oauth2client.service_account import ServiceAccountCredentials

from BCIT import BCITStudySession, Booking

# Cell References
TIMES = 2
DATES = 3

script_dir = os.path.dirname(__file__)

urls = {
    'baseUrl': 'https://studyrooms.lib.bcit.ca/',
    'loginUrl': 'https://studyrooms.lib.bcit.ca/admin.php',
    'bookUrl': 'https://studyrooms.lib.bcit.ca/edit_entry_handler.php'
}

# Load JSONs
with open(os.path.join(script_dir, r'json/headers.json')) as f:
    headers = json.load(f)
with open(os.path.join(script_dir, r'json/logins.json')) as f:
    accounts = json.load(f)
with open(os.path.join(script_dir, r'json/login_template.json')) as f:
    login_template = json.load(f)
with open(os.path.join(script_dir, r'json/book_template.json')) as f:
    book_template = json.load(f)

# Initialize gspread and get current sheet
scope = [r'https://spreadsheets.google.com/feeds', r"https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name(os.path.join(script_dir,'json/client_secret.json'), scope)
client = gspread.authorize(creds)
sheet = client.open('Room Hog').get_worksheet(1)
schedule = sheet.range('C5:I29')

# Parse the requests sheet and create a list of bookings
bookings = [Booking(date=sheet.cell(c.row, TIMES).value + sheet.cell(DATES, c.col).value + f" {sheet.cell(2, 3).value}",
                    length=c.value,
                    cell=c)
            for c in schedule if c.value.isdigit()]

# Attempt to find and book a room for each request
for booking in bookings:
    for login in accounts['logins']:
        if login['Active'] < 2:
            break
    else:
        raise Exception("Not enough accounts available, too many active bookings.")

    login_template['NewUserName'] = login['ID']
    login_template['NewUserPassword'] = login['Password']
    bcit = BCITStudySession(urls=urls,
                            loginData=login_template,
                            bookings=booking.BookingToJson(book_template),
                            headers=headers)
    room = bcit.book()
    updateRange = sheet.range(booking.cell.row, booking.cell.col, booking.cell.row + (int(booking.length) * 2)-1,
                              booking.cell.col)
    if room:
        login['Active'] = login['Active'] + 1
        booking.room = room
        for cell in updateRange:
            cell.value = booking.room
    else:
        for cell in updateRange:
            cell.value = "Not Available"
    sheet.update_cells(updateRange)
    print('\n***Booking Successful!***\n')
    print(booking)





