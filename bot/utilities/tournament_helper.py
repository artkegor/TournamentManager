import matplotlib.pyplot as plt
from PIL import Image
import io
from datetime import datetime, timedelta

# Константы
plt.rcParams['figure.dpi'] = 800
plt.rcParams['savefig.dpi'] = 800
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


# Создаем и сохраняем фото
def generate_and_save_tables(data):
    today_date = datetime.now()
    for idx, d in enumerate(data):
        date_str = today_date.strftime("%d/%m/%Y")

        fig, ax = plt.subplots(figsize=(4, 4))
        fig.patch.set_facecolor('#022027')

        table_data = [[str(x) for x in sublist] for sublist in d]
        cell_colors = [['#022027'] * len(row) for row in table_data]
        col_label_colors = ['#022027'] * len(table_data[0])
        table = ax.table(cellText=table_data,
                         cellColours=cell_colors,
                         colLabels=["Игрок {}".format(i + 1) for i in range(len(table_data[0]))],
                         colColours=col_label_colors,
                         loc='center',
                         cellLoc='center')

        for key, cell in table.get_celld().items():
            if isinstance(key, str):
                continue
            cell.set_edgecolor('#009900')

        for key, cell in table.get_celld().items():
            cell.set_text_props(color='white')

        ax.text(0.05, 0.95, date_str, transform=ax.transAxes, color='white', fontsize=14)

        plt.tight_layout()
        plt.axis('off')

        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        img = Image.open(buf)
        img.save(f'table_{idx}.png')

        today_date += timedelta(days=2)
