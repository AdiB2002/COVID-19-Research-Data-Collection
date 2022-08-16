from selenium import webdriver  
from selenium.webdriver.chrome.service import Service                  
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.firefox.firefox_binary import FirefoxBinary
import pandas as pd
import time

# AHD does block users from accessing their site after a searching up a certain amount of hospital profiles
# ways i've found to get around this include limiting daily hospital searches to under 25 or changing ip adresses once blocked

class Hospital():
    
    # constructor with default values
    def __init__(self, ahd = None, date_added = 'N/A', staffed_beds = 0, non_icu_beds = 0, icu_beds = 0, has_ahd_profile = 'NO', date_updated = 'N/A', full_address = 'N/A', address = 'N/A', city = 'N/A', zip_code = 'N/A', lat_y = 0, long_x = 0):
        self.ahd = ahd
        self.date_added = date_added 
        self.staffed_beds = staffed_beds
        self.non_icu_beds = non_icu_beds
        self.icu_beds = icu_beds
        self.has_ahd_profile = has_ahd_profile
        self.date_updated = date_updated
        self.full_address = full_address
        self.address = address
        self.city = city
        self.zip_code = zip_code
        self.lat_y = lat_y
        self.long_x = long_x
    
    # used to help add information back into dataframe by outputting as a row
    def row_output(self):
        return [self.ahd, self.date_added, self.staffed_beds, self.non_icu_beds, self.icu_beds, self.has_ahd_profile, self.date_updated, self.full_address, self.address, self.city, self.zip_code, self.lat_y, self.long_x]
        
class Scraper():
        
    # class-wide variables
    options = webdriver.FirefoxOptions()
    options.binary = FirefoxBinary("C:/Program Files/Mozilla Firefox/firefox.exe")
    driver_service = Service("C:/Computer Science/geckodriver-v0.31.0-win32/geckodriver.exe")
    browser = webdriver.Firefox(service=driver_service, options=options)
    wait = WebDriverWait(browser, 4)
    hospital_list = []
    
    # turns scraped web elements into a usable list 
    def turn_list_to_text(self, list_passed):
        for i in range(0, len(list_passed)):
            list_passed[i] = list_passed[i].text
       
    # scrapes individual hospital information
    def scrape_hospital_info(self, name_list = [], date_added = ''):
        
        # opens a browser to ahd website
        self.browser.get('https://www.ahd.com/') 
        
        # starts count
        count = 0
            
        # loops through each hospital
        for name in name_list:

            # gets hospital and ahd name
            hospital, ahd = name[0], name[1]

            # if ahd name exists set hospital to ahd name 
            if(not pd.isna(ahd)):
                hospital = ahd

            # overarching try except to cover errors that sometimes occur throughout the code
            try:
            
                # prints count
                count += 1
                print(str(count) + '/' + str(len(name_list)))
                
                # tries to enters hospital name into search bar multiple times to ensure it finds a hospital if capable
                for _ in range(4):
                    try:
                        self.browser.find_element(By.ID, "front_page-quicksearch").clear()
                        self.browser.find_element(By.ID, "front_page-quicksearch").send_keys(hospital)
                    except:
                        break
                    time.sleep(1)

                # in case captcha needs to be solved
                try:
                    time.sleep(1)
                    captcha = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="popupbody"]/table/tbody/tr[2]/td[2]/h1')))
                    captcha_dealt_with = input('Has captcha been dealt with? Enter Y to continue: ')
                except:
                    pass
                
                # scrapes last date hospital information was updated
                # the try and except is there in case a hospital entered couldn't be found cause then a proccess begins to either skip it or manually find it
                try:
                    date_updated = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/ul[1]/li')))
                    self.turn_list_to_text(date_updated)
                    date_updated = date_updated[0].split()[2]
                    has_ahd_profile = 'YES'
                except:
                    
                    # prints hospital and input to guide user through proccess of manually finding a hospital and moving on or just skipping it
                    print(hospital)
                    input_string = input('Were you able to find hospital printed above? Enter Y or N and if choosing Y only enter answer when actually on the hospital page. Also if a captcha is presented deal with that before entering your answer: ')
                    if(input_string.lower()=='y'):
                        
                        # if hospital found get date again
                        date_updated = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/ul[1]/li')))
                        self.turn_list_to_text(date_updated)
                        date_updated = date_updated[0].split()[2]
                        has_ahd_profile = 'YES'
                    
                    # if not found code to skip
                    else:
                        self.hospital_list.append(Hospital())
                        self.browser.get('https://www.ahd.com/')
                        continue
                
                # gets ahd name in case of future use
                ahd_name = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="report_wrapper"]/tbody/tr/td[2]/a/b')))
                self.turn_list_to_text(ahd_name)
                ahd_name = ahd_name[0]
                        
                # find the number of the table that has the information that needs to be scraped 
                # does this by looping through tables and looking for a specific string 
                found = False
                i = 0
                while(found == False and i < 10):
                    try:
                        test_string = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/table[' + str(i) + ']/tbody/tr[5]/td[1]')))
                        self.turn_list_to_text(test_string)
                        if(test_string[0] == 'Total Hospital'):
                            found = True
                        else:
                            i += 1
                    except:
                        i += 1

                # variable to keep track of whether to skip scraping beds               
                skip_beds = False

                # checks if staffed beds is equal to 0 
                try:
                    staffed_beds_0_check = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/table/tbody/tr/td[1]/table/tbody/tr[7]/td[2]')))
                    self.turn_list_to_text(staffed_beds_0_check)

                    # if it is sets respective variables
                    if(staffed_beds_0_check[0]=='0'):
                        staffed_beds = 0
                        non_icu_beds = 0
                        icu_beds = 0
                        skip_beds = True
                        i = 0
                
                # if an error is thrown keep going
                except Exception as e:
                    pass

                # hospital likely has no information on beds so disregard
                if(i >= 10):
                    self.hospital_list.append(Hospital())
                    self.browser.get('https://www.ahd.com/')
                    continue
                
                # if not skipping scraping beds
                if(not skip_beds):

                    # scrapes hospital staffed beds
                    staffed_beds = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/table[' + str(i) + ']/tbody/tr[5]/td[2]')))
                    self.turn_list_to_text(staffed_beds)
                    staffed_beds = int(staffed_beds[0].replace(',', ''))
                    
                    # scrapes hospital non icu beds
                    non_icu_beds = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/table[' + str(i) + ']/tbody/tr[2]/td[2]')))
                    self.turn_list_to_text(non_icu_beds)
                    non_icu_beds = int(non_icu_beds[0].replace(',', ''))
                    
                    # scrapes hospital icu beds
                    icu_beds = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/table[' + str(i) + ']/tbody/tr[3]/td[2]')))
                    self.turn_list_to_text(icu_beds)
                    icu_beds = int(icu_beds[0].replace(',', ''))
                
                # scrapes hospital full address and gets address, city, and zip code from that
                full_address = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="main"]/div[2]/table[1]/tbody/tr/td[1]/table/tbody/tr[1]/td[2]/span')))
                self.turn_list_to_text(full_address)
                full_address = full_address[0]
                address = full_address.split('\n')[0]
                city = full_address.split('\n')[1].split(',')[0]
                zip_code = full_address.split()[-1]
                
                # if address isn't in TX wrong hospital was scraped so ignore
                if(full_address.find('TX') == -1):
                    self.hospital_list.append(Hospital())
                    self.browser.get('https://www.ahd.com/')
                    continue
                
                # opens a browser to lat long website
                self.browser.get('https://getlatlong.net/')
                
                # enters hospital adress into search bar
                self.browser.find_element(By.ID, "addr").send_keys(address + ' ' + city + ' ' + ' ' + zip_code)
                self.browser.find_element(By.CLASS_NAME, "btn").click()
                
                # delay so page can load
                time.sleep(3)
                
                # gets latitude and longitude
                lat_y = self.browser.find_element(By.ID, "latbox").get_attribute('value')
                long_x = self.browser.find_element(By.ID, "lonbox").get_attribute('value')
                
                # appends all the information to a list of hospital objects
                self.hospital_list.append(Hospital(ahd_name, date_added, staffed_beds, non_icu_beds, icu_beds, has_ahd_profile, date_updated, full_address, address, city, zip_code, lat_y, long_x))
                
                # resets the broswer for next hospital
                self.browser.get('https://www.ahd.com/')
              
            # if error print the error, make hospital info default, and continue
            except Exception as e:
                print(e)
                self.hospital_list.append(Hospital())
                self.browser.get('https://www.ahd.com/')
                continue
                
        # returns list of hospital objects containing information
        return self.hospital_list

# takes information from hospital objects and adds it to dataframe
def add_info_to_dataframe(hospital_list = [], df = pd.DataFrame()):
    
    # list of columns from dataframe that information is going to be added to
    column_list = ['AHD_NAME', 'DATE_ADDED', 'STAFFED_BEDS_AHD', 'NON_ICU_BEDS_AHD', 'ICU_BEDS_AHD', 'HAS_AHD_PROFILE', 'DATE_UPDATED_AHD', 'FULL_ADDRESS', 'ADDRESS', 'CITY', 'ZIP', 'LAT_Y', 'LONG_X']
    
    # loops through columns and hospitals adding information to the dataframe 
    for i in range(0, len(column_list)):
        df_list = []
        for hospital in hospital_list:
            df_list.append(hospital.row_output()[i])
        df[column_list[i]] = df_list

    # drops columns that were in the inital dataframe that were unnecessary 
    df.drop(df.iloc[:, 26:], inplace = True, axis = 1)
    
    # returns dataframe
    return df

# splits a scraped dataframe into completed and incompleted hospitals CSVs
def split_dataframe(df = pd.DataFrame()):

    # drops the rows for each respective dataframe
    completed_df = df.drop(df.loc[df['STAFFED_BEDS_AHD']==0].index)
    incompleted_df = df.drop(df.loc[df['STAFFED_BEDS_AHD']!=0].index)

    # exports the dataframes
    completed_df.to_csv('C:/Computer Science/COVID-19-Research-Data-Collection/Completed TX Hosp ZIP Metadata.csv', index = False)
    incompleted_df.to_csv('C:/Computer Science/COVID-19-Research-Data-Collection/Incompleted TX Hosp ZIP Metadata.csv', index = False)
    
def main():
    
    # reads in TX Hospital csv file as dataframe
    df = pd.read_csv('C:/Computer Science/COVID-19-Research-Data-Collection/Copy of TX Hosp ZIP Metadata.csv')

    # gets list of hospitals from it
    hospital_name_list, ahd_name_list = list(df['PROVIDER_NAME']), list(df['AHD_NAME'])
    name_list = [[hospital_name_list[i], ahd_name_list[i]] for i in range(len(hospital_name_list))]
    
    # creates scraper object
    Scraper_obj = Scraper()
    
    # manual input for date added column
    date_added = input("Enter today's date in mm/dd/yy: ")
    
    # scrapes hospital information and takes two parameters which is list of hospital names and date added
    hospital_list = Scraper_obj.scrape_hospital_info(name_list, date_added)
    
    # quits browser when done
    Scraper_obj.browser.quit()
    
    # adds info to dataframe and takes list of hospital objects and dataframe as parameters
    df = add_info_to_dataframe(hospital_list, df)
    
    # exports df to csv
    df.to_csv('C:/Computer Science/COVID-19-Research-Data-Collection/Temporary Scraped TX Hosp ZIP Metadata.csv', index = False) 
    
    # reads in scraped data and splits it into complete and incomplete hospitals
    #df = pd.read_csv("C:/Computer Science/COVID-19-Research-Data-Collection/Scraped TX Hosp ZIP Metadata.csv")
    #split_dataframe(df)

main()