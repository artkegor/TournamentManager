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
