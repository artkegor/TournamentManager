import io
from PIL import Image
import matplotlib as mlt
import matplotlib.pyplot as plt
from collections import defaultdict
from datetime import datetime, timedelta

# Константы
mlt.use('agg')
plt.rcParams['figure.dpi'] = 400
plt.rcParams['font.family'] = 'sans-serif'


# Формируем игры
def round_robin(teams):
    if len(teams) % 2:
        return
    schedule = []
    for i in range(len(teams) - 1):
        round = []
        for j in range(len(teams) // 2):
            round.append((teams[j], teams[-j - 1]))
        teams.insert(1, teams.pop())
        schedule.append(round)

    return schedule


# Генерируем таблицу с играми
def generate_and_save_tables(games, tournament_id, group_name):
    today_date = datetime.now()
    game_id = 1
    day = 0

    table_data = []
    for idx, game_set in enumerate(games):
        date_str = (today_date + timedelta(days=2) * day).strftime("%d/%m/%Y")
        for player_tuple in game_set:
            first_player, second_player = player_tuple
            table_data.append([game_id, date_str, first_player, second_player])
            game_id += 1
        day += 1

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#022027')

    cell_colors = [['#022027'] * len(row) for row in table_data]
    col_label_colors = ['#022027'] * len(table_data[0])
    table = ax.table(cellText=table_data,
                     cellColours=cell_colors,
                     colLabels=["Номер игры", "Дата", "Первый игрок", "Второй игрок"],
                     colColours=col_label_colors,
                     loc='center',
                     cellLoc='center')

    for key, cell in table.get_celld().items():
        if isinstance(key, str):
            continue
        cell.set_edgecolor('#009900')

    for key, cell in table.get_celld().items():
        cell.set_text_props(color='white')

    ax.text(0.05, 0.95, f'Расписание турнира "{group_name}"', transform=ax.transAxes, color='white', fontsize=14)

    plt.tight_layout()
    plt.axis('off')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf)
    img.save(f'bot/utilities/data/{tournament_id}.png')


# Подсчитываем очки
def calculate_scores(games, users):
    all_games = (len(users) - 1) * 2
    scores = defaultdict(lambda: {"score": 0, "games_results": {"wins": 0, "draws": 0, "losses": 0},
                                  "games_left": {"played": 0, "all": all_games}})
    if not games:
        sorted_scores = None
        for i in users:
            scores[i] = {"score": 0, "games_results": {"wins": 0, "draws": 0, "losses": 0},
                         "games_left": {"played": 0, "all": all_games}}
            sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1]['score'], reverse=True))

            place = 1
            for player_id, player_data in sorted_scores.items():
                player_data['place'] = place
                place += 1

        return sorted_scores

    for game in games:
        if 'first_game_results' in game:
            try:
                first_player = game['first_game_results']['first_player']
                second_player = game['first_game_results']['second_player']

                first_score = int(game['first_game_results']['score'].split(':')[0])
                second_score = int(game['first_game_results']['score'].split(':')[1])
                if first_score > second_score:
                    scores[first_player]['score'] += 3
                    scores[first_player]['games_results']['wins'] += 1
                    scores[second_player]['games_results']['losses'] += 1
                elif first_score < second_score:
                    scores[second_player]['score'] += 3
                    scores[second_player]['games_results']['wins'] += 1
                    scores[first_player]['games_results']['losses'] += 1
                else:
                    scores[first_player]['score'] += 1
                    scores[second_player]['score'] += 1
                    scores[first_player]['games_results']['draws'] += 1
                    scores[second_player]['games_results']['draws'] += 1

                scores[first_player]['games_left']['played'] += 1
                scores[second_player]['games_left']['played'] += 1
            except:
                if game['first_player'] not in scores:
                    scores[game['first_player']] = {"score": 0, "games_results": {"wins": 0, "draws": 0, "losses": 0},
                                                    "games_left": {"played": 0, "all": all_games}}
                if game['second_player'] not in scores:
                    scores[game['second_player']] = {"score": 0, "games_results": {"wins": 0, "draws": 0, "losses": 0},
                                                     "games_left": {"played": 0, "all": all_games}}

        if 'second_game_results' in game:
            try:
                first_player = game['second_game_results']['first_player']
                second_player = game['second_game_results']['second_player']

                first_score = int(game['second_game_results']['score'].split(':')[0])
                second_score = int(game['second_game_results']['score'].split(':')[1])

                if first_score > second_score:
                    scores[first_player]['score'] += 3
                    scores[first_player]['games_results']['wins'] += 1
                    scores[second_player]['games_results']['losses'] += 1
                elif first_score < second_score:
                    scores[second_player]['score'] += 3
                    scores[second_player]['games_results']['wins'] += 1
                    scores[first_player]['games_results']['losses'] += 1
                else:
                    scores[first_player]['score'] += 1
                    scores[second_player]['score'] += 1
                    scores[first_player]['games_results']['draws'] += 1
                    scores[second_player]['games_results']['draws'] += 1

                scores[first_player]['games_left']['played'] += 1
                scores[second_player]['games_left']['played'] += 1
            except:
                if game['first_player'] not in scores:
                    scores[game['first_player']] = {"score": 0, "games_results": {"wins": 0, "draws": 0, "losses": 0},
                                                    "games_left": {"played": 0, "all": all_games}}

                if game['second_player'] not in scores:
                    scores[game['second_player']] = {"score": 0, "games_results": {"wins": 0, "draws": 0, "losses": 0},
                                                     "games_left": {"played": 0, "all": all_games}}

    for i in users:
        if i not in scores:
            scores[i] = {"score": 0, "games_results": {"wins": 0, "draws": 0, "losses": 0},
                         "games_left": {"played": 0, "all": all_games}}

    sorted_scores = dict(sorted(scores.items(), key=lambda item: item[1]['score'], reverse=True))

    place = 1
    for player_id, player_data in sorted_scores.items():
        player_data['place'] = place
        place += 1

    return sorted_scores


# Создаем табличку текущих результатов
def save_tournament_results(tournament_id, group_title, results):
    table_data = []
    for player, details in results.items():
        result_str = f'{details["games_results"]["wins"]}-{details["games_results"]["draws"]}-{details["games_results"]["losses"]}'
        games_left = f'{details["games_left"]["played"]}/{details["games_left"]["all"]}'
        table_data.append([details['place'], player, games_left, result_str, details['score']])

    fig, ax = plt.subplots(figsize=(10, 8))
    fig.patch.set_facecolor('#022027')

    cell_colors = [['#022027'] * len(row) for row in table_data]
    col_label_colors = ['#022027'] * len(table_data[0])
    table = ax.table(cellText=table_data,
                     cellColours=cell_colors,
                     colLabels=["Место", "Имя", "Игры", "Результаты", "Очки"],
                     colColours=col_label_colors,
                     loc='center',
                     cellLoc='center')

    for key, cell in table.get_celld().items():
        if isinstance(key, str):
            continue
        cell.set_edgecolor('#009900')
        cell.set_text_props(color='white')

    ax.text(0.05, 0.95, f'Текущие результаты турнира "{group_title}"', transform=ax.transAxes, color='white',
            fontsize=14)

    plt.tight_layout()
    plt.axis('off')

    buf = io.BytesIO()
    fig.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    img = Image.open(buf)

    img.save(f'bot/utilities/data/res_{tournament_id}.png')
