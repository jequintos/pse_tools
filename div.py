import re

from urllib import request, parse
from bs4 import BeautifulSoup
from pprint import pprint

MONEY_REGEX_PATTERN = r'\d+(\.\d+)?'

def get_id_from_url(url):
    return url[url.rindex('=')+1:]

def get_company_code_and_latest_price(id_):
    soup = soup_open_page('http://edge.pse.com.ph/companyPage/stockData.do?cmpy_id={}'.format(id_))
    return soup.find('option').get_text(), float(soup.find(string='Last Traded Price').parent.parent.find('td').get_text().strip())

def get_latest_company_div(id_):
    # Returns (ex-date, value, dividend string)
    COL_NO_FOR_DIVIDEND_RATE = 2
    COL_NO_FOR_EX_DIVIDEND_DATE = 3

    # Dividend page is fetched from a web service
    soup = soup_open_page('http://edge.pse.com.ph/companyPage/dividends_and_rights_list.ax?DividendsOrRights=Dividends', {'cmpy_id': id_})
    rows = soup.find('table').find_all('tr')
    if len(rows) > 1: # There's a header row!
        first_row_cols = rows[1].find_all('td')
    latest_ex_div_date = first_row_cols[COL_NO_FOR_EX_DIVIDEND_DATE].get_text()
    div_string_template = first_row_cols[COL_NO_FOR_DIVIDEND_RATE].get_text()
    div_rates = [get_money_value_from_string(div_string_template)] # put it on a list as we are going to process this later
    for row in rows[2:]: # if there are more rows, append them
        cols = row.find_all('td')
        if cols[COL_NO_FOR_EX_DIVIDEND_DATE].get_text() == latest_ex_div_date:
            div_rates.append(get_money_value_from_string(cols[COL_NO_FOR_DIVIDEND_RATE].get_text()))
    # div_rates
    div_rate = round(sum([float(i) for i in div_rates]), 4)
    dividend_string = replace_money_value_in_string(div_rate, div_string_template)
    return latest_ex_div_date, div_rate, dividend_string
        

        
def soup_open_page(url, data=None):
    if data and type(data) is dict:
        encoded_data = parse.urlencode(data).encode()
        req = request.Request(url, encoded_data)
        content = request.urlopen(req)
    else:
        content = request.urlopen(url).read()
    return BeautifulSoup(content)

def get_money_value_from_string(s):
    p = re.compile(MONEY_REGEX_PATTERN)
    m = p.search(s)
    if m:
        return m.group()
    return 0 # We can't find the value so give it 0 instead (to avoid None-type exception)

def replace_money_value_in_string(val, s):
    p = re.compile(MONEY_REGEX_PATTERN)
    return p.sub(str(val), s)


if __name__ == '__main__':
    url = 'http://edge.pse.com.ph/'
    content = request.urlopen(url).read()
    soup = BeautifulSoup(content)

    table = soup.find(id='dividends_div')
    companies_with_div = [
        {
            'company': row.find('a').get_text(),
            'id': get_id_from_url(row.find('a')['href']),
            'type': row.find_all('td', class_='alignC')[0].get_text(),
        }
        for row in table.find_all('tr')[1:]
    ]

    for company in companies_with_div:
        company['code'], company['current_price'] = get_company_code_and_latest_price(company['id'])
        company['ex_div_date'], company['div_rate'], company['div_rate_str'] = get_latest_company_div(company['id'])
        company['div_percent'] = company['div_rate'] / company['current_price'] * 100 if '%' not in company['div_rate_str'] else company['div_rate']
        company['div_percent_gain'] = company['div_percent'] - 1.19 

    filtered_5div = [company for company in companies_with_div if company['div_percent'] >= 5]
    pprint(filtered_5div)


