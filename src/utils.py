import pandas as pd
import os
import glob
from datetime import datetime
from dateutil.relativedelta import relativedelta
from pypdf import PdfReader
import re

import package_root


DATA_PATH = os.path.join(package_root._root, 'data')


##### Utilies functions for data preprocessing #####
def date_parser(data: pd.DataFrame, 
                start_date: str = None, 
                end_date: str = None, 
                year: int = None, 
                month: int = None):
    
    current_time = datetime.now()

    if start_date and end_date:
        subset = data[(data['Date'] >= start_date) & (data['Date'] <= end_date)]
        date_string = f'{start_date} to {end_date}'
    elif start_date:
        subset = data[data['Date'] >= start_date]
        date_string = f'Everything After {start_date}'
    elif end_date:
        subset = data[data['Date'] <= end_date]
        date_string = f'Everything Up to {end_date}'
    elif year and not month:
        subset = data[data['Date'].dt.year == year]
        date_string = f'{year}'
    else:
        year = year if year else current_time.year
        month = month if month else current_time.month
        subset = data[(data['Date'].dt.year == year) & (data['Date'].dt.month == month)]
        date_string = f'{year}-{month}'

    return subset, date_string


def write_file(file, df):
    if os.path.exists(file):
        existing_data = pd.read_csv(file)
        existing_data['Date'] = pd.to_datetime(existing_data['Date'], format='%Y-%m-%d')
        df = pd.concat([existing_data, df])
    
    df.to_csv(file, index=False)


##### Function that read and preprocess input data #####
def extract_credit_card_data():
    path = os.path.join(DATA_PATH, '2025-05-15_transaction_download.csv')
    df = pd.read_csv(path)

    # add grocery category
    df.loc[df['Description'].str.contains('GIANT|ALDI|WEGMANS|WHOLEFDS|TRADER JOE|LIDL|HARRIS TEETER'), 'Category'] = 'Groceries'

    df['Date'] = pd.to_datetime(df['Transaction Date'], format='%Y-%m-%d')
    df.dropna(axis=0, subset=['Debit'], inplace=True)
    df.drop(['Transaction Date', 'Posted Date', 'Card No.', 'Description', 'Credit'], axis=1, inplace=True)
 
    file = os.path.join(DATA_PATH, 'credit_card_data.csv')
    # file = '../data/credit_card_data.csv'
    if os.path.exists(file):
        existing_data = pd.read_csv(file)
        existing_data['Date'] = pd.to_datetime(existing_data['Date'], format='%Y-%m-%d')
        df = pd.concat([existing_data, df])
        # TODO: Delete file

    # delete file
    df.to_csv(file, index=False)


def parse_bank_pdf(pdf):
    reader = PdfReader(pdf)

    for idx in range(len(reader.pages)):
        page = reader.pages[idx]

        content = page.extract_text()

        date_range = re.search(r'For the period (\d\d\/\d\d\/\d\d\d\d) to (\d\d\/\d\d\/\d\d\d\d)', content)
        if date_range:
            start_date = date_range.group(1)
            end_date = date_range.group(2)

        summary = re.search(r'Balance Summary[\S\s]*Ending\nbalance([\S\s]*)Average monthly', content)
        if summary:
            totals = summary.group(1).replace(',','').strip().split(' ')[1:]
            totals = [end_date] + totals[-1:] + totals[:-1]

            df = pd.DataFrame([totals], columns=['Date', 'Total', 'Added', 'Lost'])
            df['Date'] = pd.to_datetime(df['Date'], format='%m/%d/%Y')

    path = os.path.join(DATA_PATH, 'totals.csv')
    write_file(path, df)
    return start_date, end_date


def parse_bank_csv(csv, start_date, end_date):
    data = pd.read_csv(csv)
    data['Date'] = pd.to_datetime(data['Date'], format='%m/%d/%Y')
    data = data.sort_values(by='Date')
    data.drop(['Balance', 'Category'], axis=1, inplace=True)
    data.loc[data['Description'].str.lower().str.contains('zel to albert secen|sheffield court|comcast'), 'Category'] = 'Rent'
    data.loc[data['Description'].str.lower().str.contains('capital one|chase credit'), 'Category'] = 'Credit Card'
    data.loc[data['Description'].str.lower().str.contains('drexel'), 'Category'] = 'Tuition'
    data.loc[data['Description'].str.lower().str.contains('transfer'), 'Category'] = 'Transfer'
    data.loc[data['Description'].str.lower().str.contains('leidos'), 'Category'] = 'Paycheck'
    data.loc[data['Category'].isna(), 'Category'] = 'Misc'

    deducations = data[data['Deposits'].isna()]
    deducations = deducations[(deducations['Date'] >= start_date) & (deducations['Date'] <= end_date)]
    deducations['Amount'] = deducations['Withdrawals'].str.replace('$', '').str.replace(',', '').astype(float)
    deducations.drop(['Withdrawals', 'Deposits', 'Description'], axis=1, inplace=True)
    deducations = deducations[['Date', 'Amount', 'Category']]

    path = os.path.join(DATA_PATH, 'deductions.csv')
    write_file(path, deducations)

    additions = data[data['Withdrawals'].isna()]
    additions = additions[(additions['Date'] >= start_date) & (additions['Date'] <= end_date)]
    additions['Amount'] = additions['Deposits'].str.replace('$', '').str.replace(',', '').astype(float)
    additions.drop(['Withdrawals', 'Deposits', 'Description'], axis=1, inplace=True)
    additions = additions[['Date', 'Amount', 'Category']]

    path = os.path.join(DATA_PATH, 'additions.csv')
    write_file(path, additions)


def extract_bank_data():
    path = os.path.join(DATA_PATH, 'bank_data')
    statement_csv = glob.glob(f'{path}/*.csv')
    statement_pdf = glob.glob(f'{path}/*.pdf')

    if len(statement_pdf) < 0 or len(statement_csv) < 0:
        print('Error')
    else:
        start_date, end_date = parse_bank_pdf(statement_pdf[0])
        parse_bank_csv(statement_csv[0], start_date, end_date)


##################################################################################

def get_lookback_data(filename, n_months=None):
    path = os.path.join(DATA_PATH, filename)
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    year = df.iloc[-1]['Date'].year
    month = df.iloc[-1]['Date'].month
    
    if n_months:
        dt = datetime(year=year, month=month, day=1)
        new_dt = dt - relativedelta(months=n_months)
        start_date = new_dt.strftime('%Y-%m-%d')

        subset, _ = date_parser(df, start_date=start_date)
    else:
        subset, _ = date_parser(df, year=year, month=month)

    return subset


def get_spending():
    path = os.path.join(DATA_PATH, 'deductions.csv')
    df = pd.read_csv(path)
    df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    year = df.iloc[-1]['Date'].year
    month = df.iloc[-1]['Date'].month

    subset, _ = date_parser(df, year=year, month=month)
    group = subset.groupby(['Category'])['Amount'].sum()
    rets = {'Rent': 0, 'Credit Card': 0, 'Misc': 0}
    for k, _ in rets.items():
        try:
            rets[k] = float(group[k])
        except:
            continue

    return tuple(rets.values())


def get_totals():
    # TODO: Update to exclude things like transfers
    path = os.path.join(DATA_PATH, 'totals.csv')
    totals_df = pd.read_csv(path)

    latest = totals_df.iloc[-1]

    return latest['Added'] - latest['Lost']


def get_income(cum_type, n_months):
    # path = os.path.join(DATA_PATH, 'additions.csv')
    # df = pd.read_csv(path)
    # df['Date'] = pd.to_datetime(df['Date'], format='%Y-%m-%d')

    # year = df.iloc[-1]['Date'].year
    # month = df.iloc[-1]['Date'].month

    # subset, _ = date_parser(df, year=year, month=month)

    subset = get_lookback_data('additions.csv', n_months=n_months)
    # subset
    # subset = subset[subset['Category'] != 'Transfer']
    # subset
    # subset.groupby(['Date'])['Amount'].sum()
    if cum_type:
        group = subset.groupby(['Category'])['Amount'].sum()
    else:
        group = subset.groupby(['Category'])['Amount'].mean()
    income = float(group['Paycheck'])

    return income


def update_investment_data(input_data):
    investments_path = os.path.join(DATA_PATH, 'investments.csv')

    current_time = datetime.now()
    day = current_time.date()
    cols = ['Date', 'Amount', 'Category']
    data = [[day, v, k] for k, v in input_data.items() if v]
    df = pd.DataFrame(data, columns=cols)

    write_file(investments_path, df)


def get_total_assets():
    investments_path = os.path.join(DATA_PATH, 'investments.csv')
    totals_path = os.path.join(DATA_PATH, 'totals.csv')

    investment_df = pd.read_csv(investments_path)
    investment_df['Date'] = pd.to_datetime(investment_df['Date'], format='%Y-%m-%d')
    investments = ['etrade', 'leidos', '401k', 'cambridge']
    grouping = investment_df.loc[investment_df.groupby('Category').Date.idxmax()]
    total_investments = grouping[grouping['Category'].isin(investments)]['Amount'].sum()

    bank_df = pd.read_csv(totals_path)
    bank_df['Date'] = pd.to_datetime(bank_df['Date'], format='%Y-%m-%d')
    bank_total = bank_df.iloc[-1]['Total']

    return total_investments+bank_total

    
    


    

