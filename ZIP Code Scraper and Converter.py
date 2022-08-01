from selenium import webdriver  
from selenium.webdriver.chrome.service import Service                  
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from selenium.webdriver.chrome.options import Options

# have to keep rerunning code until you get onto a good run which can usually take a few tries
# the code will either not even scrape the zip codes or scrape the zip codes and give error shortly after
# scraping might need to be done in segments cause of error around when 500-700 zip codes reached
# simply change what portion of zip codes is being scraped when looping through zip codes (list slicing is easiest)

class Zip_Code():
    
    # constructor
    def __init__(self, zip_code_type = 'N/A', zip_code = 'N/A', converted_zip_code = 'N/A'):
        self.zip_code_type = zip_code_type
        self.zip_code = zip_code
        self.converted_zip_code = converted_zip_code
    
    # returns variables in a list so it can be added to dataframe
    def row_output(self):
        return [self.zip_code_type, self.zip_code, self.converted_zip_code]

class Scraper():
    
    # class-wide variables that set up browser and creates a list for zip code object
    executable_path = Service('C:/Computer Science/chromedriver_win32/chromedriver.exe')
    chrome_options = Options()
    chrome_options.add_argument('--disable-dev-shm-usage') 
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    browser = webdriver.Chrome(options = chrome_options, service = executable_path)
    wait = WebDriverWait(browser, 5)
    zip_code_list = []
    
    # turns scraped web elements into a usable list 
    def turn_list_to_text(self, list_passed):
        for i in range(0, len(list_passed)):
            list_passed[i] = list_passed[i].text
            
    # scrapes zip codes and converts to residential zip codes
    def scrape_zip_code(self):
        
        # opens a browser to texas gazetteer website
        # while loop and try except needed to ensure it opens and scrapes zip codes because of tab crashing
        works = False
        while(works == False):
            try:
                
                # opens browser to website
                self.browser.get('https://texas.hometownlocator.com/zip-codes/') 
                
                # scrapes all zip codes
                zip_codes = self.wait.until(EC.presence_of_all_elements_located((By.ID, 'zipLinksList')))
                self.turn_list_to_text(zip_codes)
                zip_codes = zip_codes[0].split()
                
                # prints that it scraped them and sets works = True
                print("Got " + str(len(zip_codes)) + " ZIP codes\n")
                works = True
            except:
                pass
            
        # begins count and loops through zip codes
        count = 0
        for zip_code in zip_codes:
            
            # increases count and prints it
            count += 1
            print(str(count) + '/' + str(len(zip_codes)))
            
            # try except to make sure it searches each zip code by its link
            try:
                
                # goes to the link of each zip code
                self.browser.get('https://texas.hometownlocator.com/zip-codes/data,zipcode,' + str(zip_code) + '.cfm')
            
            # if error prints error and moves onto the next zip code
            except:
                self.zip_code_list.append(Zip_Code(zip_code = zip_code))
                print('ERROR')
                continue
            
            # gets the type of zip code
            zip_code_type = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bodycontainer"]/div[4]/div[2]/div[4]/ul[1]/li[1]')))
            self.turn_list_to_text(zip_code_type)
            zip_code_type = zip_code_type[0]
            
            # in some cases zip code type messes up so accounting for that 
            if(zip_code_type == 'Accounting Jobs'):
                zip_code_type = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bodycontainer"]/div[4]/div[1]/div[4]/ul[1]/li[1]')))
                self.turn_list_to_text(zip_code_type)
                zip_code_type = zip_code_type[0]
            
            # formats zip code type 
            zip_code_type = zip_code_type.split(': ')[1]
            
            # zip code is same for standard so disregard those 
            if(zip_code_type == 'STANDARD'):
                converted_zip_code = zip_code
            else:
                
                # tries to get the new zip code of po box and unique single identity 
                # try except needed because for some of them there is no need to convert and this throws an error
                try:
                    converted_zip_code = self.wait.until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="bodycontainer"]/div[4]/div[2]/ol[1]/a')))
                    self.turn_list_to_text(converted_zip_code)
                    converted_zip_code = converted_zip_code[0].split()[2]
                except:
                    converted_zip_code = zip_code
            
            # creates a zip code object and appends to the list
            self.zip_code_list.append(Zip_Code(zip_code_type, zip_code, converted_zip_code))
                
            # resets browser after each zip code
            self.browser.get('https://texas.hometownlocator.com/zip-codes/') 
        
        # returns list of zip code objects 
        return self.zip_code_list

# exports zip codes to csv 
def export_to_csv(zip_code_list = []):
    
    # creates the dataframe
    df = pd.DataFrame(columns = ['ZIP_Code_Type', 'ZIP_Code', 'Converted_ZIP_Code'])
    
    # loops through zip code objects and adds to dataframe
    for zip_code_obj in zip_code_list:
        df.loc[len(df)] = zip_code_obj.row_output()
        
    # exports df to csv
    df.to_csv('C:/Computer Science/COVID-19-Research-Data-Collection/Temporary Converted ZIP Codes Data.csv', index = False) 

# verifies the scraped data
def verify_data():
    
    # reads in the csv file as dataframe
    df = pd.read_csv("C:/Computer Science/COVID-19-Research-Data-Collection/Converted ZIP Codes Data.csv")
    
    # drops columns that were in the dataframe that were unnecessary 
    df.drop(df.iloc[:, 3:], inplace = True, axis = 1)
    
    # prints unique zip codes scraped and this should equal 2598 since there are that many zip codes in TX
    print(str(len(set(df['ZIP_Code']))) + ' Unique ZIP Codes Scraped')
    
def main():
    
    # scraper object
    Scraper_obj = Scraper()
    
    # scrape and convert zip codes and takes no parameters
    # try except just to get results in case of error
    try:
        zip_code_list = Scraper_obj.scrape_zip_code()
    except Exception as e:
        print(e)
        zip_code_list = Scraper_obj.zip_code_list
    
    # quits the browser when done
    Scraper_obj.browser.quit()
    
    # exports to csv and takes list of zip codes objects as parameter
    export_to_csv(zip_code_list)
    
    # verifies scraped data after all scraping is done and takes no parameters
    #verify_data()

main()