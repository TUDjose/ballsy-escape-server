import io
import time
import os
from flask import *
import multiprocessing
import json
import base64
import pandas as pd
import numpy as np
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import requests
import itertools
from collections import defaultdict


matplotlib.use('TkAgg')
app = Flask(__name__, template_folder='templates')
current_analytics_filename = os.path.join(os.path.expanduser('~'), "AppData", "LocalLow", "Monumentum Studios", "Ballsy Escape", "Analytics", "GameData.sav")
full_analytics_filename = r'FullAnalytics.csv'
full_data = dict()

def merge_dict_lists(dict_list):
    merged_dict = defaultdict(list)
    for d in dict_list:
        for k, v in d.items():
            merged_dict[k].extend(v)
    return merged_dict

def save_data(data1, data2):
    global full_data
    data1.update(data2)
    full_data = data1
    save_data_to_file()


def save_data_to_file():
    if len(full_data) > 0:
        with open(full_analytics_filename, 'a') as f:
            f.write(json.dumps(full_data) + '\n')

def show_analytics():
    player = []
    all_players = {}
    names = []
    with open(full_analytics_filename, 'r') as f:
        for line in f:
            data = json.loads(line)
            player.append({k:v for k,v in data.items() if k != 'Position'})

    for d in player:
        if d['Name'] not in names:
            names.append(d['Name'])

    for d in player:
        if d['Name'] not in all_players:
            all_players[d['Name']] = []
        all_players[d['Name']].append(d)

    x = [max(all_players[n], key=lambda x: x['Score']) for n in names]

    return sorted(x, key=lambda x: x['Score'], reverse=True)



@app.route('/plot', methods=['GET', 'POST'])
def show_data():
    with open(full_analytics_filename, 'r') as f:
        data = [json.loads(line) for line in f]

    scores = [d['Score'] for d in data]
    deaths = [d['Deaths'] for d in data]
    kills = [d['Kills'] for d in data]
    coins = [d['Coins'] for d in data]
    gems = [d['Gems'] for d in data]
    gadgets = [d['Gadgets'] for d in data]
    damage_taken = [d["DamageTaken"] for d in data]
    analysis = [scores, deaths, kills, coins, gems, gadgets, damage_taken]
    names = ['Scores', 'Deaths', 'Kills', 'Coins', 'Gems', 'Gadgets', 'Damage Taken']

    positions = [dict(itertools.islice(d.items(), 8, None)) for d in data]
    merged_positions = dict(merge_dict_lists(positions))

    # Create a Matplotlib figure
    fig, ax = plt.subplots(7 + len(merged_positions), 1)
    fig.set_figheight(20)
    fig.set_figwidth(10)
    fig.tight_layout(pad=3.0)

    for i in range(0, 7):
        ax[i].hist(analysis[i], bins=15)
        ax[i].set_title(names[i])

    for i, name in enumerate(merged_positions):
        for j in range(0, len(merged_positions[name])):
            ax[i + 7].scatter(merged_positions[name][j]['x'], merged_positions[name][j]['z'])
        ax[i + 7].set_title(name)


    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    figure_data = base64.b64encode(buf.getvalue()).decode('utf-8')

    return render_template('plot.html', figure_data=figure_data)


@app.route('/leaderboard', methods=['GET', 'POST'])
def table():
    # Create a list of rows for the table
    data = show_analytics()
    # Pass the table to the HTML template
    return render_template('leaderboard.html', data=data)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('home.html')


@app.route('/receive_json', methods=['POST'])
def receive_json():
    data = request.get_json()
    analytics = data['playerAnalytics']['values'][0]
    positions = {}
    for i, pos in enumerate(data['playerPosAnalytics']['values']):
        positions[data['playerPosAnalytics']['keys'][i]] = pos['Position']
    save_data(analytics, positions)
    return 'Success'

@app.route('/receive_data_from_flask', methods=['GET', 'POST'])
def send_json():
    data = {"Name": "Jose", "Score": -50, "Deaths": 1, "Kills": 0, "Coins": 0, "Gems": 0, "Gadgets": 0, "DamageTaken": 100, "Position": [{"x": 44.908447265625, "y": 0.8999989032745361, "z": 54.571712493896484}]}
    response = requests.post('http://localhost:5000/receive_data_from_flask', json=data)
    return response


# @app.route('/download')
# def download_csv():
#     with open(full_analytics_filename, 'r') as f:
#         csv_data = f.read()
#
#     response = make_response(csv_data)
#     response.headers['Content-Type'] = 'text/csv'
#     response.headers['Content-Disposition'] = f'attachment; filename={full_analytics_filename}'
#     return response


if __name__ == '__main__':
    app.run()
