import matplotlib.pyplot as plt
from PIL import Image
import io
from datetime import datetime, timedelta

# Константы
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
