import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as BraveService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType
import logging

def construct_url(division, day, month, year):
    if day < 10:
        day = f'0{day}'
    url = f"https://www.11v11.com/league-tables/{division}/{day}-{month}-{year}/"
    return url

options = webdriver.ChromeOptions()
options.binary_location = "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser" # Path to Brave Browser (this is the default)

driver = webdriver.Chrome(options=options, service=BraveService(ChromeDriverManager(chrome_type=ChromeType.BRAVE).install()))

df = pd.read_csv("./results/output/results_df.csv", parse_dates=["game_date"])

df['new_league_name'] = df.competition.str.lower().str.replace(" ", "-", regex=False).str.replace("(", "", regex=False).str.replace(")", "", regex=False)

df['year'] = df.game_date.dt.year
df['month'] = df.game_date.dt.month_name().str.lower()
df['day'] = df.game_date.dt.day

df['table_url'] = df.apply(lambda row: construct_url(row.new_league_name, row.day, row.month, row.year), axis=1)

table_urls = df[(df.game_type == 'League') & (df.new_league_name != 'national-league')].table_url.to_list()

tables_df = pd.DataFrame()
for url in table_urls:
    try:    
        driver.get(url)

        doc = driver.page_source
        table = pd.read_html(doc)[0]
        df = pd.DataFrame(table)
        df = df[['Pos', 'Team', 'Pld', 'W', 'D', 'L', 'GF', 'GA', 'Pts']]
        df['index_no'] = df.index + 1
        df['url'] = url
        tables_df = pd.concat([tables_df, df])
    except:
        logging.basicConfig(filename='error.log', encoding='utf-8', level=logging.DEBUG)
        logging.warning('Failed trying to scrape %s', url)
     
driver.quit()

try:
    tables_df.Pos = tables_df.Pos.astype(str).str.replace("doRowNumer();", "", regex=False)
except AttributeError:
    pass

tables_df.to_csv("./data/all_league_tables.csv", index = False)