import requests
import json
import re

from bs4 import BeautifulSoup
from datetime import datetime, timedelta


rooms = {
    26: 'SW1-1104',
    27: 'SW1-1105',
    28: 'SW1-1106',
    29: 'SW1-2110',
    30: 'SW1-2111',
    31: 'SW1-2112',
    32: 'SW1-2113',
    33: 'SW1-2186',
    34: 'SW1-2187',
    35: 'SW1-2513',
    36: 'SW1-2515',
    37: 'SW1-2517',
    38: 'SW1-2519'
}


class BCITStudySession:
    def __init__(self,
                 urls,
                 loginData,
                 bookings,
                 headers,
                 **kwargs):
        self.urls = urls
        self.loginData = loginData
        self.bookings = bookings
        self.headers = headers
        self.session = requests.Session()
        self.login(**kwargs)

    def login(self, **kwargs):
        self.session.headers.update(self.headers)
        res = self.session.post(self.urls['loginUrl'], data=self.loginData, **kwargs)

        # Test login
        if res.text.lower().find(self.loginData["NewUserName"].lower()) < 0:
            raise Exception(f"could not log onto BCIT '{self.urls['loginUrl']}'"
                            " (did not find successful login string)")
        else:
            print(f"\n***Login as {self.loginData['NewUserName']} successful!***\n")

    def book(self):
        page = self.session.get(self.urls['baseUrl']+f'day.php?year={self.bookings["start_year"]}&'
                                                            f'month={self.bookings["start_month"]}&'
                                                              f'day={self.bookings["start_day"]}&'
                                                             f'area=4') # **Add multiple areas later
        # **Change to use booking obj
        s_hr = int(self.bookings["start_seconds"]) // 3600
        s_m = int(self.bookings["start_seconds"]) % 3600 // 60
        e_hr = int(self.bookings["end_seconds"]) // 3600
        e_m = int(self.bookings["end_seconds"]) % 3600 // 60
        length = abs((e_hr - s_hr) + ((e_m - s_m) / 60))

        soup = BeautifulSoup(page.text, features='html.parser')
        emptyEntries = soup.find_all('td', {'class': 'new'})
        emptyStarts = [entry for entry in emptyEntries if f'hour={s_hr}&minute={s_m}' in entry.find('a')['href']]
        availableRooms = []

        for t in emptyStarts:
            seq = t.find_next_siblings('td', {'class': 'new'}, limit=(length * 2) - 1)
            if len(seq) == (length * 2 - 1):
                room = re.search(r'room=(\d+)', t.find('a')['href']).group(1)
                availableRooms.append(room)
                # print(f"Room {rooms[int(room)]} is available!\n")

        # **add room preference, check if room was booked?
        if availableRooms:
            print("Room Found!")
            self.bookings['rooms[]'] = availableRooms[0]
            self.bookings['create_by'] = self.loginData['NewUserName']
            b = self.session.post('https://studyrooms.lib.bcit.ca/edit_entry_handler.php', data=self.bookings)
            print(b.text)
            self.session.close()
            return rooms[int(availableRooms[0])]
        else:
            self.session.close()
            return False


class Booking:
    def __init__(self, date, length, cell, account=('', '')):
        print(date)
        self.length = length
        self.account = account
        self.startDate = datetime.strptime(date, '%I:%M %p %m/%d %Y')
        self.endDate = self.startDate + timedelta(hours=int(length))
        self.startSeconds = int(self.startDate.hour) * 3600 + int(self.startDate.minute) * 60
        self.endSeconds = int(self.endDate.hour) * 3600 + int(self.endDate.minute) * 60
        self.room = ''
        self.cell = cell

    def __repr__(self):
        return(f'Date: {str(self.startDate.date())}\n'
               f'Time: {str(self.startDate.hour)}:{str(self.startDate.minute)} to '
               f'{str(self.endDate.hour)}:{str(self.endDate.minute)} \n'
               f'Room: {self.room}\n')

    def BookingToJson(self, bookTemplate):
        bookTemplate['start_day'] = self.startDate.day
        bookTemplate['start_month'] = self.startDate.month
        bookTemplate['start_year'] = self.startDate.year
        bookTemplate['start_seconds'] = self.startSeconds
        bookTemplate['end_day'] = self.endDate.day
        bookTemplate['end_month'] = self.endDate.month
        bookTemplate['end_year'] = self.endDate.year
        bookTemplate['end_seconds'] = self.endSeconds

        return bookTemplate



