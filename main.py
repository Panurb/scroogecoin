#!/usr/bin/python

import argparse
import time
from datetime import datetime, timedelta
import calendar

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pycoingecko import CoinGeckoAPI


def iso_to_unix(str, hours=0):
    date = datetime.fromisoformat(str) + timedelta(hours=hours)
    return int(calendar.timegm(date.timetuple()))
    

def unix_to_date(timestamp):
    return datetime.utcfromtimestamp(timestamp)


def get_data(from_timestamp, to_timestamp):
    cg = CoinGeckoAPI()
    data = cg.get_coin_market_chart_range_by_id(
        id='bitcoin', 
        vs_currency='eur', 
        from_timestamp=str(from_timestamp),
        to_timestamp=str(to_timestamp))

    prices = np.array(data['prices'])
    times = [unix_to_date(t / 1000) for t in prices[:, 0]]
    
    # Take only the value closest to midnight
    indices = [i for i, t in enumerate(times) if t.hour == 0]
    
    dates = [times[i].date() for i in indices]
    prices = prices[indices, 1]
    volumes = np.array(data['total_volumes'])[indices, 1]
    
    return dates, prices, volumes
    
    
def longest_downturn(prices):
    max_days = 0
    days = 0
    for i in range(1, len(prices) - 1):
        max_days = max(max_days, days)
        if prices[i] < prices[i - 1]:
            days += 1
        else:
            days = 0
            
    # Include the start date in the downturn
    if (max_days > 0):
        max_days += 1

    return max_days
    
    
def highest_volume(dates, volumes):
    i = np.argmax(volumes)
    return dates[i].isoformat(), volumes[i]
    
    
def best_buy_sell_dates(dates, prices):
    buy_index = 0
    sell_index = 0
    min_index = 0
    max_diff = -np.inf
    
    for i in range(1, len(dates) - 1):
        if prices[i] < prices[min_index]: 
            min_index = i
        else:
            diff = prices[i] - prices[min_index]
            if diff > max_diff:
                max_diff = diff
                buy_index = min_index
                sell_index = i

    if max_diff > 0:
        return dates[buy_index].isoformat(), dates[sell_index].isoformat()

    return '-', '-'
    
    
# For testing purposes
def plot_values(dates, values):
    plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.gca().xaxis.set_major_locator(mdates.MonthLocator())
    plt.plot(dates, values)
    plt.gcf().autofmt_xdate()
    plt.show()

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('start', type=str, help='start date in ISO format (YYYY-mm-dd)')
    parser.add_argument('end', type=str, help='end date in ISO format (YYYY-mm-dd)')
    parser.add_argument('--plot', action='store_true', help='plot a price graph')
    
    args = parser.parse_args()
    
    try:
        from_date = iso_to_unix(args.start)
        to_date = iso_to_unix(args.end, 1)
    except ValueError:
        parser.error('invalid date')
    
    dates, prices, volumes = get_data(from_date, to_date)
        
    print(f'Longest downturn: {longest_downturn(prices)} days')
    date, volume = highest_volume(dates, volumes)
    print(f'Highest trading volume: {volume:,.2f} EUR on {date}')
    buy_date, sell_date = best_buy_sell_dates(dates, prices)
    print(f'Best buy date: {buy_date}, sell date: {sell_date}')
    
    if args.plot:
        plot_values(dates, prices)


if __name__ == '__main__':
    main()
