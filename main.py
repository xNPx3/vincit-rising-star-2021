import requests
import datetime
import json
import argparse


def main(args):
    if args.date_to < args.date_from:
        print("Parameter 'date_to' is before 'date_from'. Check your inputs and try again.")
        exit()

    l = False
    # check if time range is more than 90 days
    if args.date_to - args.date_from < datetime.timedelta(days=90):
        l = True
        extended = args.date_to + datetime.timedelta(days=90)

    try:
        url = f'https://api.coingecko.com/api/v3/coins/{args.currency.lower()}/market_chart/range?vs_currency=eur&from={args.date_from.timestamp()}&to={extended.timestamp() if l else args.date_to.timestamp()}'
        r = requests.get(url)
        data = json.loads(r.text)
    except requests.exceptions.RequestException as ex:
        raise SystemExit(ex)

    try:
        if l:
            end = (extended-args.date_from).days - 90 + 1
            prices = data['prices'][0:end]
            volumes = data['total_volumes'][0:end]
        else:
            prices = data['prices']
            volumes = data['total_volumes']
    except KeyError:
        print('There is no prices available for that currency.')
        exit()

    trend = downward_trend(prices)

    print(
        f"{args.currency.title()}'s price decreased {trend} days in a row for the selected time range.")

    timestamp, max_volume = trading_volume(volumes)
    volume_date = datetime.datetime.utcfromtimestamp(timestamp / 1000).date()

    print(
        f"{args.currency.title()}'s highest trading volume was {round(max_volume, 2)}€ on {volume_date}.")

    profit = best_profit(prices)
    if profit['buy'] < profit['sell']:
        buy_date = datetime.datetime.utcfromtimestamp(profit['buy'] / 1000).date()
        sell_date = datetime.datetime.utcfromtimestamp(profit['sell'] / 1000).date()
        print(f"Buy {args.currency.title()} on {buy_date} and sell on {sell_date} to maximize profits.")
    else:
        print(f"You shouldn't buy or sell {args.currency.title()} on the selected time period.")





def downward_trend(prices):
    decrease = []
    temp = 0
    for i, d in enumerate(prices):
        if i > 0:
            if d[1] < prices[i - 1][1]:
                temp += 1
            else:
                decrease.append(temp)
                temp = 0

    decrease.append(temp)
    return max(decrease)


def trading_volume(volumes):
    max_volume = max(x[1] for x in volumes)
    timestamp = [x[0] for x in volumes if x[1] == max_volume][0]

    return timestamp, max_volume

def best_profit(prices):
    profit = []
    for timestamp1, price1 in prices:
        for timestamp2, price2 in prices:
            diff = price2 - price1
            if diff > 0:
                profit.append({
                    "buy": timestamp1,
                    "sell": timestamp2,
                    "buy_price": price1,
                    "sell_price": price2,
                    "difference": diff
                })

    max_diff = max(x['difference'] for x in profit)
    return [x for x in profit if x['difference'] == max_diff][0]


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Dates are accepted in ISO 8601 format. (YYYY-MM-DD)")
    parser.add_argument('date_from', type=datetime.datetime.fromisoformat, help="Start date of the time period.")
    parser.add_argument('date_to', type=datetime.datetime.fromisoformat, help="End date of the time period.")
    parser.add_argument('-c', '--currency', nargs="?", type=str, help="The cryptocurrency used in the calculations. Default is Bitcoin", default="bitcoin")
    args = parser.parse_args()
    main(args)