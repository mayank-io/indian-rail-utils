#!/usr/bin/python
__author__ = 'mayank-io'

from lxml import etree
from random import randint
import argparse
import requests
from tidylib import tidy_document
from lxml import etree
from BeautifulSoup import BeautifulSoup

def strip_tags(html, invalid_tags):
    soup = BeautifulSoup(html)

    for tag in invalid_tags:
        for match in soup.findAll(tag):
            match.replaceWithChildren()

    return soup

class PnrStatus(object):
    def __init__(self, pnr=None, passengers=[], chartingStatus=None):
        self.pnr = pnr;
        self.passengers = passengers;
        self.chartingStatus = chartingStatus
    def __str__(self):
        s = ""
        for p in self.passengers:
            s = s + str(p) + "\n"
        s.rstrip("\n")
        return "PNR: %s, Charting Status: %s, Passengers:\n%s"%(self.pnr, self.chartingStatus, s)

class Passenger(object):
    def __init__(self, passengerName=None, bookingStatus=None, currentBookingStatus=None):
        self.passengerName = passengerName;
        self.bookingStatus = bookingStatus
        self.currentBookingStatus = currentBookingStatus

    def __str__(self):
        return  "Passenger: %s, Current status: %s, Status at time of booking: %s"%(self.passengerName, self.currentBookingStatus, self.bookingStatus)


#curl 'http://www.indianrail.gov.in/cgi_bin/inet_pnrstat_cgi.cgi'
# -H 'Cookie: _ga=GA1.3.805941002.1388382456'
# -H 'Origin: http://www.indianrail.gov.in'
# -H 'Accept-Encoding: gzip,deflate,sdch'
# -H 'Host: www.indianrail.gov.in'
# -H 'Accept-Language: en-US,en;q=0.8'
# -H 'User-Agent: Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36'
# -H 'Content-Type: application/x-www-form-urlencoded'
# -H 'Accept: text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
# -H 'Cache-Control: max-age=0'
# -H 'Referer: http://www.indianrail.gov.in/pnr_Enq.html'
# -H 'Connection: keep-alive'
# --data 'lccp_pnrno1=4256979700&lccp_cap_val=56758&lccp_capinp_val=56758&submit=Get+Status'
# --compressed

parser = argparse.ArgumentParser(description='Fetch status of PNR from indianrail.gov.in.')
parser.add_argument('pnr', type=str, help='10 digit PNR number')
args = parser.parse_args()
pnr = args.pnr
new_captcha = randint(10000, 99999)

url = "http://www.indianrail.gov.in/cgi_bin/inet_pnrstat_cgi.cgi"
pnr_param_name = "lccp_pnrno1"
captcha_ref_value_param_name = "lccp_cap_val"
captcha_input_value_param_name = "lccp_capinp_val"


payload = "lccp_pnrno1=%s&lccp_cap_val=%d&lccp_capinp_val=%d&submit=Get+Status"%(pnr,new_captcha,new_captcha)
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Encoding": "gzip,deflate,sdch",
    "Accept-Language": "en-US,en;q=0.8",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Content-Type": "application/x-www-form-urlencoded",
    "Host": "www.indianrail.gov.in",
    "Referer": "http://www.indianrail.gov.in/pnr_Enq.html",
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/31.0.1650.63 Safari/537.36",
}

response = requests.post(url, data=payload, headers=headers)

invalid_tags = ['b', 'i', 'u']
cleaned_up_soup = strip_tags(response.text, invalid_tags)

data = cleaned_up_soup.prettify()

data = "".join(line.strip() for line in data.split("\n"))

parser = etree.HTMLParser()
tree = etree.XML(data, parser)
status_table = tree.xpath("//*[@id='center_table']")
enquired_pnr = tree.xpath("/html/body/table/tbody/tr/td/table/tbody/tr[1]/td/table/tbody/tr[3]/td/table/tbody/tr/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[2]/td[2]/table/tbody/tr[2]/td[1]/table[1]/tbody/tr[3]/td")

rows = iter(status_table[0])
headers = [col.text for col in next(rows)]

pnrStatus = PnrStatus()
pnrStatus.pnr=enquired_pnr

for row in rows:
    #{'* Current Status': 'CNF', 'S. No.': 'Passenger 1', 'Booking Status': 'CNF  ,GN'}
    values = [col.text for col in row]
    status_row = dict(zip(headers, values))
    # print status_row
    s_no = status_row.get('S. No.')
    booking_status=status_row.get('Booking Status')
    current_status=status_row.get('* Current Status')
    if isinstance(s_no, str):
        if  s_no.startswith("Charting"):
            pnrStatus.chartingStatus = booking_status
        if s_no.startswith("Passenger"):
            passenger = Passenger(s_no, booking_status, current_status)
            pnrStatus.passengers.append(passenger);

print pnrStatus


