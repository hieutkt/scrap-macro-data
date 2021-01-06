# /usr/bin/python3

import sys
import time
import datetime
import re
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException
import pandas as pd


# Find the correct path to the browser driver
if sys.platform.startswith("win"):
    # CHROME_DRIVER = "./bin/chromedriver.exe"  #On Windows
    FIREFOX_DRIVER = "./bin/geckodriver.exe"
elif sys.platform.startswith("linux"):
    # CHROME_DRIVER = "./bin/chromedriver" #On Linux
    FIREFOX_DRIVER = "./bin/geckodriver"
else:
    print("Failed to find driver!")


# Initialize the browser
BROWSER_OPTIONS = Options()
# BROWSER = webdriver.Chrome(executable_path=CHROME_DRIVER,
#                            options=BROWSER_OPTIONS)
BROWSER = webdriver.Firefox(executable_path=FIREFOX_DRIVER,
                            options=BROWSER_OPTIONS)
BROWSER.set_window_size(1024, 768)

# As user for starting day and ending day
start_date = input('Enter start date in YYYY-MM-DD format: ')
end_date = input('Enter end date in YYYY-MM-DD format: ')

# Convert input strings into datetime format
start = datetime.datetime.strptime(start_date, "%Y-%m-%d")
end = datetime.datetime.strptime(end_date, "%Y-%m-%d")

# Create a list of dates from `start` to `end`
datelist = pd.date_range(start_date, end_date)


def get_exchge_rate(datelist):
    """Get exchange rate for a list of dates"""
    print("Scraping for Exchange Rate")
    exchgerate_url = "https://www.vietcombank.com.vn/ExchangeRates/"
    BROWSER.get(exchgerate_url)
    output = pd.DataFrame(columns = ["Date", "Exchange_Rate"])
    time.sleep(5) #change time(second) depending on internet speed
    # This website requires dates in "%d/%m/%Y" format
    datelist = datelist.strftime("%d/%m/%Y")
    for index_, date_str in enumerate(datelist):
        # d = datelist1[0]
        # Find input box and write date in "%d/%m/%Y"
        dateinput = BROWSER.find_element_by_css_selector('#txttungay')
        dateinput.clear()
        dateinput.send_keys(date_str)
        dateinput.send_keys(Keys.ENTER)
        dateinput.send_keys(Keys.ENTER)
        # Find the element that contains exchange rate and extracts for text
        while True:
            try:
                exchge_rate = BROWSER.find_element_by_xpath('//*[@id="ctl00_Content_ExrateView"]/tbody/tr[22]/td[5]').text
                break
            except:
                # print("Element not found, sleep for 1 sec")
                time.sleep(1)
                continue
        # Reformat the rate found
        exchge_rate = float(exchge_rate.replace(",", ""))
        print("Found: Exch.Rate for " + date_str + " is: " + str(exchge_rate))
        # Append that exchange rate string into the `output` list
        output = output.append({"Date" : datelist[index_],
                                "Exchange_Rate" : exchge_rate},
                               ignore_index = True)
    # Return list of exch.rates
    return(output)


def get_interbankrate(datelist):
    """Get interbank rates - Oneweek and overnight"""
    print("Scraping for Interbank Rates")
    interbank_rate_url = 'https://www.sbv.gov.vn/webcenter/portal/vi/menu/rm/ls/lsttlnh'
    BROWSER.get(interbank_rate_url)
    output = pd.DataFrame(columns = ["Date", "Inter_Overnight", "Inter_Oneweek"])
    # Query for 20 days at a time
    for date_range in [datelist[i:i + 20] for i in range(0, len(datelist), 20)]:
        date_range = date_range.strftime("%d/%m/%Y")
        print("Scraping from ", date_range[0], " to ", date_range[-1])
        while True:
            try:
                startinput = BROWSER.find_element_by_css_selector(
                    r'#T\:oc_5531706273region\:id1\:\:content')
                startinput.clear()
                startinput.send_keys(date_range[0])
                endinput = BROWSER.find_element_by_css_selector(
                    r'#T\:oc_5531706273region\:id4\:\:content')
                endinput.clear()
                endinput.send_keys(date_range[-1])
                gobutton = BROWSER.find_element_by_css_selector(
                    r'#T\:oc_5531706273region\:cb1')
                gobutton.click()
                time.sleep(10)
                gobutton.click() #Click twice, just to be sure
            except StaleElementReferenceException as e:
                print("Found a stale element, move on...")
                time.sleep(10)
                break
            except Exception as e:
                print(e)
                BROWSER.refresh()
                # BROWSER.get(interbank_rate_url)
                continue
            break
        # Wait until listings show up
        days_perpage = 0
        while days_perpage == 0:
            time.sleep(5)
            days_perpage = len(BROWSER.find_elements_by_css_selector('.x10m'))
            print(days_perpage, 'found')
        # Go over each link and scrap for data inside
        for i in range(days_perpage):
            info = {}
            while True:
                try:
                    day = BROWSER.find_elements_by_css_selector('.x10m')[i]
                    info['Date'] = day.find_element_by_css_selector("span.x1q").text
                    print('Date: ', info['Date'])
                except:    
                    time.sleep(1)
                    continue
                break
            day.find_element_by_css_selector('a.x2fe').click()
            while True:
                try:
                    overnight = BROWSER.find_element_by_css_selector(r'#T\:oc_5531706273region\:j_id__ctru7pc9 > table > tbody > tr > td:nth-child(2) > table > tbody > tr:nth-child(4) > td:nth-child(2) > span').text
                    oneweek = BROWSER.find_element_by_css_selector(r'#T\:oc_5531706273region\:j_id__ctru7pc9 > table > tbody > tr > td:nth-child(2) > table > tbody > tr:nth-child(5) > td:nth-child(2) > span').text
                except:
                    time.sleep(1)
                    continue
                break
            # Reformat strings and convert to float
            info['Inter_Overnight'] = float(overnight.replace(",", "."))
            print("Found: Interbank Rate Overnight: ", info['Inter_Overnight'])
            info['Inter_Oneweek'] = float(oneweek.replace(",", "."))
            print("Found: Interbank Rate Oneweek: ", info['Inter_Oneweek'])
            # Append data to output
            output = output.append(info, ignore_index=True)
            # Find the 'Quay lại' button
            BROWSER.find_element_by_css_selector(r'#T\:oc_5531706273region\:j_id__ctru11pc9').click()
            print('Going back to date listings')
    return(output)


def get_centralrate(datelist):
    """Get central bank rates"""
    print("Scraping for Central Rates")
    central_rate_url = 'https://www.sbv.gov.vn/TyGia/faces/TyGiaTrungTam.jspx'
    BROWSER.get(central_rate_url)
    output = pd.DataFrame(columns = ["Date", "Central_Rate"])
    for date_range in [datelist[i:i + 20] for i in range(0, len(datelist), 20)]:
        date_range = date_range.strftime("%d/%m/%Y")
        print("Scraping from ", date_range[0], " to ", date_range[-1])
        while True:
            try:
                startinput = BROWSER.find_element_by_css_selector(r'#pt1\:r2\:0\:id1\:\:content')
                startinput.clear()
                startinput.send_keys(date_range[0])
                endinput = BROWSER.find_element_by_css_selector(r'#pt1\:r2\:0\:id4\:\:content')
                endinput.clear()
                endinput.send_keys(date_range[-1])
                gobutton = BROWSER.find_element_by_css_selector(r'a.button-submit.af_commandLink')
                gobutton.click()
                time.sleep(5)
                gobutton.click() #Click twice, just to be sure
            except Exception as e:
                print(e)
                BROWSER.refresh()
                # BROWSER.get(central_rate_url)
                time.sleep(10)
                break
            break
        # Wait until listings show up
        days_perpage = 0
        while days_perpage == 0:
            time.sleep(5)
            days_perpage = len(BROWSER.find_elements_by_css_selector('.af_table_data-row'))
            print(days_perpage, 'found')
        # Go over each link and scrap for data inside
        for i in range(days_perpage):
            info = {}
            while True:
                try:
                    day = BROWSER.find_elements_by_css_selector('.af_table_data-row')[i]
                    info['Date'] = day.find_element_by_css_selector('span.af_inputDate_content').text
                    print('Date: ', info['Date'])
                except:
                    time.sleep(1)
                    continue
                break
            day.find_element_by_css_selector('a.af_commandLink.button-view').click()
            while True:
                try:
                    central = BROWSER.find_element_by_css_selector(r'#pt1\:r2\:1\:j_id_id7pc3 > table:nth-child(4) > tbody:nth-child(1) > tr:nth-child(1) > td:nth-child(2) > table:nth-child(2) > tbody:nth-child(1) > tr:nth-child(6) > td:nth-child(3) > span:nth-child(1)').text
                except:
                    time.sleep(1)
                    continue
                break
            info['Central_Rate'] = re.sub("[^0-9]", "", central)
            print("Found: Central Rate is: ", info["Central_Rate"])
            # Append data to output
            output = output.append(info, ignore_index=True)
            # Find the 'Quay lại' button
            BROWSER.find_element_by_css_selector(r'a.button-back.af_commandLink').click()
            print('Going back to date listings')
    return(output)


# Scraping
df_exchge_rate = get_exchge_rate(datelist)
df_interbank_rate = get_interbankrate(datelist)
df_central_rate = get_centralrate(datelist)

# Join data into one dataframe
df = pd.DataFrame(datelist.strftime("%d/%m/%Y"), columns = ["Date"])
df = df.join(df_exchge_rate.set_index("Date"), on = "Date")
df = df.join(df_interbank_rate.set_index("Date"), on = "Date")
df = df.join(df_central_rate.set_index("Date"), on = "Date")

# Reconvert date
df["Date"] = pd.to_datetime(df["Date"], format="%d/%m/%Y")

# Write data to csv
df.to_csv("macro-data.csv")
