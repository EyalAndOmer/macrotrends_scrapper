import json
import os
import random
import re
from itertools import cycle
from time import sleep

import pandas as pd

import requests
from bs4 import BeautifulSoup


def get_stocks():
    url = 'https://www.macrotrends.net/stocks/stock-screener'

    headers = {
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Cache-Control': 'max-age=0',
        'Cookie': 'cf_clearance=b_VOuztB3b3IvKs7qrbZuABBkYOtgC7AvXg5dIQcPfw-1713902041-1.0.1.1-GUqkX9yqewtt90e_ME37xxS6w5J.Qv6NQL1w6__NENkLhpmWABc0r3JeMDCHtzuE.y.55b8wKqP_RpV4agqDsA',
        'If-Modified-Since': 'Tue, 23 Apr 2024 16:04:40 GMT',
        'Priority': 'u=0, i',
        'Sec-Ch-Ua': '"Chromium";v="124", "Brave";v="124", "Not-A.Brand";v="99"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Model': '""',
        'Sec-Ch-Ua-Platform': '"Windows"',
        'Sec-Ch-Ua-Platform-Version': '"15.0.0"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'cross-site',
        'Sec-Fetch-User': '?1',
        'Sec-Gpc': '1',
        'Upgrade-Insecure-Requests': '1',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }

    # Send a GET request
    response = requests.get(url, headers=headers)

    # Parse the HTML content of the page with BeautifulSoup
    soup = BeautifulSoup(response.content, 'html.parser')

    # Select the second script tag in the HTML
    script_tags = soup.find_all('script')

    for script_tag in script_tags:
        # Use a regular expression to find the variable assignment for originalData
        match = re.search(r'var chartData = (\[.*?\])', script_tag.string.lstrip() if script_tag.string else '')

        # If the variable was found in the JavaScript code
        if match:
            try:
                # Try to parse the JSON data and convert it into a Python object
                original_data = json.loads(match.group(1))
                # If successful, print the data and break the loop
                df = pd.DataFrame(original_data)

                # Exclude the 'name_link' column if it exists
                if 'name_link' in df.columns:
                    df = df.drop(columns=['name_link'])

                # Save the dataframe to a CSV file
                df.to_csv('data.csv', index=False)
                break
            except json.JSONDecodeError:
                # If an error occurred while decoding the JSON, continue with the next script tag
                continue


headers = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.9',
    'Cache-Control': 'max-age=0',
    'Cookie': 'cf_clearance=F73AE9stnOzSiMVFJt.y_Fm2.VQZAQoa7vyAWq1clbs-1713970758-1.0.1.1-mpMdwjP5dgVlWjvgSmlCj_1CDM9y9tUOQ945.BRRJQH1AJE13mgKsODM1XI5Zvk92P.mu3pBjCjheeGq38b7jA',
    'If-Modified-Since': 'Tue, 23 Apr 2024 16:04:40 GMT',
    'Priority': 'u=0, i',
    'Sec-Ch-Ua': '"Chromium";v="124", "Brave";v="124", "Not-A.Brand";v="99"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Model': '""',
    'Sec-Ch-Ua-Platform': '"Windows"',
    'Sec-Ch-Ua-Platform-Version': '"15.0.0"',
    'Sec-Fetch-Dest': 'document',
    'Sec-Fetch-Mode': 'navigate',
    'Sec-Fetch-Site': 'cross-site',
    'Sec-Fetch-User': '?1',
    'Sec-Gpc': '1',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
}


def make_request(url: str, proxy):
    response = requests.get(url, headers=headers, proxies=proxy)

    if not response.ok:
        raise Exception(response.reason)

    return response.text


# Prices tab fetches
def stock_price_history(company_symbol: str, company_name: str, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/stock-price-history'

    response_data = make_request(url, session)

    # Assuming 'response_data' is the HTML content received from a request
    soup = BeautifulSoup(response_data, 'html.parser')

    # Find the first table with class 'historical_data_tables'
    # Find the first table with class 'historical_data_table table'
    table = soup.find('table', {'class': 'historical_data_table table'})

    # Get table headers, skip the first one
    headers = [header.text for header in table.find_all('th')][1:]

    # Get table rows
    rows = table.find_all('tr')

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() if col.text.strip() != '' else ' ' for col in cols]
        # Only add to table_data if cols is not empty
        if cols:
            table_data.append([col for col in cols if col])  # Get rid of empty values

    # Convert list of lists into DataFrame
    df = pd.DataFrame(table_data, columns=headers)
    df.to_csv(f'{company_symbol}-stock_price_history.csv', index=False)


def market_cap(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/assets/php/market_cap.php?t={company_symbol}'
    response_data = make_request(url, session)

    soup = BeautifulSoup(response_data, 'html.parser')

    # Select the second script tag in the HTML
    script_tags = soup.find_all('script')

    for script_tag in script_tags:
        # Use a regular expression to find the variable assignment for originalData
        match = re.search(r'var chartData = (\[.*?\]);', script_tag.string if script_tag.string else '')

        # If the variable was found in the JavaScript code
        if match:
            try:
                # Try to parse the JSON data and convert it into a Python object
                original_data = json.loads(match.group(1))
                # If successful, print the data and break the loop
                df = pd.DataFrame(original_data)

                # Exclude the 'name_link' column if it exists
                if 'name_link' in df.columns:
                    df = df.drop(columns=['name_link'])

                # Save the dataframe to a CSV file
                df.to_csv(f'{company_symbol}-market_cap.csv', index=False)
                break
            except json.JSONDecodeError:
                # If an error occurred while decoding the JSON, continue with the next script tag
                continue


# Financials fetches

def financial_statement_table_parser(response_data):
    soup = BeautifulSoup(response_data, 'html.parser')

    # Select the second script tag in the HTML
    script_tags = soup.find_all('script')

    for script_tag in script_tags:
        # Use a regular expression to find the variable assignment for originalData
        match = re.search(r'var originalData = (\[.*?\]);', script_tag.string if script_tag.string else '')

        # If the variable was found in the JavaScript code
        if match:
            try:
                original_data = json.loads(match.group(1))

                # If successful, create a DataFrame from the data
                df = pd.DataFrame(original_data)

                # Remove rows where 'field_name' contains a <span> tag
                df = df[~df['field_name'].str.contains('</span>')]

                # Extract the text from the a tag in the 'field_name' column
                df['field_name'] = df['field_name'].apply(lambda x: BeautifulSoup(x, 'html.parser').text)

                # Remove the second column (assuming the DataFrame has at least two columns)
                df = df.drop(df.columns[1], axis=1)

                return df
            except json.JSONDecodeError:
                continue


def no_header_table_parser(response_data):
    # Assuming 'response_data' is the HTML content received from a request
    soup = BeautifulSoup(response_data, 'html.parser')

    # Find the first table with class 'historical_data_tables'
    # Find the first table with class 'historical_data_table table'
    table = soup.find_all('table', {'class': 'historical_data_table table'})[1]

    # Get table headers, skip the first one
    headers = ['date', 'value']

    # Get table rows
    rows = table.find_all('tr')

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() if col.text.strip() != '' else ' ' for col in cols]
        # Only add to table_data if cols is not empty
        if cols:
            table_data.append(cols)  # Get rid of empty values

    # Convert list of lists into DataFrame
    df = pd.DataFrame(table_data, columns=headers)

    return df


def margin_table_parser(response_data):
    # Assuming 'response_data' is the HTML content received from a request
    soup = BeautifulSoup(response_data, 'html.parser')

    # Find the first table with class 'historical_data_tables'
    # Find the first table with class 'historical_data_table table'
    table = soup.find('table', {'class': 'table'})

    # Get table headers, skip the first one
    headers = [header.text for header in table.find_all('th')][1:]

    # Get table rows
    rows = table.find_all('tr')

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() if col.text.strip() != '' else ' ' for col in cols]
        # Only add to table_data if cols is not empty
        if cols:
            table_data.append([col for col in cols if col])  # Get rid of empty values

    # Convert list of lists into DataFrame
    df = pd.DataFrame(table_data, columns=headers)
    return df


def income_statement(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/financial-statements'
    response_data = make_request(url, session)

    df = financial_statement_table_parser(response_data)
    if df is not None:
        df.to_csv(f'{company_symbol}-income_statement.csv', index=False)


def balance_sheet(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/balance-sheet'
    response_data = make_request(url, session)

    df = financial_statement_table_parser(response_data)
    if df is not None:
        df.to_csv(f'{company_symbol}-balance_sheet.csv', index=False)


def cash_flow_statement(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/cash-flow-statement'
    response_data = make_request(url, session)

    df = financial_statement_table_parser(response_data)

    if df is not None:
        df.to_csv(f'{company_symbol}-cash_flow_statement.csv', index=False)


def key_financial_ratios(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/financial-ratios'
    response_data = make_request(url, session)

    df = financial_statement_table_parser(response_data)

    if df is not None:
        df.to_csv(f'{company_symbol}-key_financial_ratios.csv', index=False)


# Revenue and profit
def revenue(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/revenue'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_revenue.csv', index=False)


def gross_profit(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/gross-profit'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_gross_profit.csv', index=False)


def operating_income(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/operating-income'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_operating_income.csv', index=False)


def ebidta(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/ebitda'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_ebidta.csv', index=False)


def net_income(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/net-income'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_net_income.csv', index=False)


def eps(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/eps-earnings-per-share-diluted'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_eps.csv', index=False)


def shares_outstanding(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/shares-outstanding'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_shares_outstanding.csv', index=False)


# Assets and liabilities
def total_assets(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/total-assets'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_total_assets.csv', index=False)


def cash_on_hand(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/cash-on-hand'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_cash_on_hand.csv', index=False)


def long_term_dept(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/long-term-debt'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_long_term_dept.csv', index=False)


def total_liabilities(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/total-liabilities'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_total_liabilities.csv', index=False)


def share_holder_equity(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name.lower()}/total-share-holder-equity'

    response_data = make_request(url, session)
    df = no_header_table_parser(response_data)

    df.to_csv(f'{company_symbol}-quarterly_share_holder_equity.csv', index=False)


# Margins
def profit_margins(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/assets/php/fundamental_metric.php?t={company_symbol}&chart=profit-margin'

    response_data = make_request(url, session)
    soup = BeautifulSoup(response_data, 'html.parser')

    # Select the second script tag in the HTML
    script_tags = soup.find_all('script')

    for script_tag in script_tags:
        # Use a regular expression to find the variable assignment for originalData
        match = re.search(r'var chartData = (\[.*?])', script_tag.string.lstrip() if script_tag.string else '')

        # If the variable was found in the JavaScript code
        if match:
            try:
                original_data = json.loads(match.group(1))

                # If successful, create a DataFrame from the data
                df = pd.DataFrame(original_data)
                df.columns = ['Date', 'TTM Gross Margin', 'TTM Operating Margin', "TTM Net Margin"]

                df.to_csv(f'{company_symbol}-profit_margins.csv', index=False)
            except json.JSONDecodeError:
                continue


def gross_margin(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/gross-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-gross_margin.csv', index=False)


def operating_margin(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/operating-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-operating_margin.csv', index=False)


def ebitda_margin(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/ebitda-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-ebitda_margin.csv', index=False)


def pre_tax_margin(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/pre-tax-profit-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-pre_tax_margin.csv', index=False)


def net_margin(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/net-profit-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-net_margin.csv', index=False)


def pe_ratio(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/gross-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-pe_ratio.csv', index=False)


def ps_ratio(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/gross-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-ps_ratio.csv', index=False)


def price_book_ratio(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/gross-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-price_book_ratio.csv', index=False)


def price_fcf_ratio(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/gross-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-price_fcf_ratio.csv', index=False)


def net_worth(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/gross-margin'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-net_worth.csv', index=False)


# Other ratios
def current_ratio(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/current-ratio'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-current_ratio.csv', index=False)


def quick_ratio(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/quick-ratio'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-quick_ratio.csv', index=False)


def debt_equity_ratio(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/debt-equity-ratio'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-debt_equity_ratio.csv', index=False)


def roe(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/roe'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-roe.csv', index=False)


def roa(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/roa'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-roa.csv', index=False)


def roi(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/roi'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-roi.csv', index=False)


def return_tang_equity(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/return-on-tangible-equity'

    response_data = make_request(url, session)
    df = margin_table_parser(response_data)
    df.to_csv(f'{company_symbol}-return_tang_equity.csv', index=False)


# Other metrics
def dividend_yield(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/assets/php/dividend_yield.php?t={company_symbol}'

    response_data = make_request(url, session)
    soup = BeautifulSoup(response_data, 'html.parser')

    # Select the second script tag in the HTML
    script_tags = soup.find_all('script')

    for script_tag in script_tags:
        # Use a regular expression to find the variable assignment for originalData
        match = re.search(r'var chartData = (\[.*?]);', script_tag.string.lstrip() if script_tag.string else '')

        # If the variable was found in the JavaScript code
        if match:
            try:
                original_data = json.loads(match.group(1))

                # If successful, create a DataFrame from the data
                df = pd.DataFrame(original_data)
                df.columns = ['Date', 'Stock Price', 'TTM Divident Payout', "TTM Dividend Yield"]

                df.to_csv(f'{company_symbol}-dividend_yield.csv', index=False)
            except json.JSONDecodeError:
                continue


def employee_count(company_symbol, company_name, session):
    url = f'https://www.macrotrends.net/stocks/charts/{company_symbol}/{company_name}/number-of-employees'
    response_data = make_request(url, session)

    soup = BeautifulSoup(response_data, 'html.parser')

    # Find the first table with class 'historical_data_tables'
    # Find the first table with class 'historical_data_table table'
    table = soup.find_all('table', {'class': 'historical_data_table table'})[0]

    # Get table headers, skip the first one
    headers = ['date', 'number_of_employees']

    # Get table rows
    rows = table.find_all('tr')

    table_data = []
    for row in rows:
        cols = row.find_all('td')
        cols = [col.text.strip() if col.text.strip() != '' else ' ' for col in cols]
        # Only add to table_data if cols is not empty
        if cols:
            table_data.append([''.join(col.split(',')) for col in cols if col])  # Get rid of empty values

    # Convert list of lists into DataFrame
    df = pd.DataFrame(table_data, columns=headers)

    df.to_csv(f'{company_symbol}-employee_count.csv', index=False)


def scrape_companies():
    functions = [stock_price_history, market_cap, income_statement, balance_sheet, cash_flow_statement,
                 key_financial_ratios,
                 revenue, gross_profit, operating_income, ebidta, net_income, eps, shares_outstanding, total_assets,
                 cash_on_hand,
                 long_term_dept, total_liabilities, share_holder_equity, profit_margins, gross_margin, operating_margin,
                 ebitda_margin,
                 pre_tax_margin, net_margin, pe_ratio, ps_ratio, price_book_ratio, price_fcf_ratio, net_worth,
                 current_ratio,
                 quick_ratio, debt_equity_ratio, roe, roa, roi, return_tang_equity, dividend_yield, employee_count]
    stocks = pd.read_csv("data.csv")

    curr_fun = 1
    total_fun = len(functions)

    proxy_list = [
    ]

    proxy_pool = cycle(proxy_list)

    # Create a new directory called 'stocks'
    if not os.path.exists('stocks'):
        os.makedirs('stocks')

    stocks_dir = os.path.abspath('stocks')

    os.chdir('stocks')

    for stock, company_name in zip(stocks['ticker'], stocks['comp_name']):
        # For each stock, create a subdirectory with the name from the company_name variable
        company_path = os.path.join(company_name)
        if not os.path.exists(company_path):
            os.makedirs(company_path)

        # Change the current working directory to the newly created subdirectory
        os.chdir(company_path)
        index = 0
        curr_fun = 1
        proxy_str = next(proxy_pool)
        proxy = {"http": f"http://{proxy_str.split(',')[1]}:{proxy_str.split(',')[2]}@{proxy_str.split(',')[0]}",
                 "https": f"http://{proxy_str.split(',')[1]}:{proxy_str.split(',')[2]}@{proxy_str.split(',')[0]}"}
        while index != total_fun:
            try:
                if (index + 1) % 5 == 0:  # Check if it's time to reset the session
                    proxy_str = next(proxy_pool)
                    proxy = {
                        "http": f"http://{proxy_str.split(',')[1]}:{proxy_str.split(',')[2]}@{proxy_str.split(',')[0]}",
                        "https": f"http://{proxy_str.split(',')[1]}:{proxy_str.split(',')[2]}@{proxy_str.split(',')[0]}"}

                functions[index](stock, company_name, proxy)
                sleep(random.uniform(0.2, 1))
            except Exception as e:
                if e.args[0] == 'Not Found':
                    print(f'Function {curr_fun}/{total_fun} - {functions[index].__name__}  done.')
                    curr_fun += 1
                    index += 1
                print(e)
                proxy_str = next(proxy_pool)
                proxy = {
                    "http": f"http://{proxy_str.split(',')[1]}:{proxy_str.split(',')[2]}@{proxy_str.split(',')[0]}",
                    "https": f"http://{proxy_str.split(',')[1]}:{proxy_str.split(',')[2]}@{proxy_str.split(',')[0]}"}
                sleep(random.uniform(0.2, 1))
                continue

            print(f'Function {curr_fun}/{total_fun} - {functions[index].__name__}  done.')
            curr_fun += 1
            index += 1
        curr_fun = 1
        print(f'Company {company_name} done.')

        # Change the current working directory back to the 'stocks' directory
        os.chdir(stocks_dir)


if __name__ == '__main__':
    scrape_companies()
