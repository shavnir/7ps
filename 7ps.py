import random
from tqdm import tqdm


PLAYER_NAMES = [ f"Player {x}" for x in range(1,73)]

INVERSE_DRAFT_MAPPING = { 0:5, 1:4, 2:3, 3:2, 4:1, 5:0}

class PlayerData:
    name: str = ""
    r1_table_num: int = 0
    r1_draft_slot: int = 0
    r1_opponents: list[str] = []
    r1_win : bool = False

    r2_table_num: int = 0
    r2_draft_slot: int = 0
    r2_opponents: list[str] = []
    r2_win: bool = False

    def __init__(self, name: str):
        self.name = name
        self.r1_table_num = -1
        self.r1_draft_slot = -1
        self.r1_opponents = []
        self.r1_win = False

        self.r2_table_num = -1
        self.r2_draft_slot = -1
        self.r2_opponents = []
        self.r2_win = False

class TournamentTable:
    def __init__(self, table_number: int, round: int):
        self.table_number = table_number
        self.round = round
        self.seats = {}
        self.winner_name = ""
        for x in range(6):
            self.seats[x] = None

r2_algo_efficiency  = {}

def simulate_tournament():

    player_data_map = {}
    for name in PLAYER_NAMES:
        player_data_map[name] = PlayerData(name)

    # Step 1 - shuffle the players and assign them to tables 1-12 and draft slots A-F
    random.shuffle(PLAYER_NAMES)

    r1_tables = []

    for idx in range(1,13):
        r1_tables.append(TournamentTable(idx, 1))

    for index, player in enumerate(PLAYER_NAMES):
        table = (index // 6)
        draft_slot = index % 6
        player_data_map[player].r1_table_num = index // 6
        player_data_map[player].r1_draft_slot = index % 6
        player_data_map[player].r2_draft_slot = INVERSE_DRAFT_MAPPING[index % 6]

        r1_tables[table].seats[draft_slot] = player


    # Next let's go ahead and do per table processing
    for table in r1_tables:
        draft_slot_that_wins = random.randint(0,5)
        winner = table.seats[draft_slot_that_wins]
        table.winner_name = winner
        player_data_map[winner].r1_win = True

        player_name_list = [x for _, x in table.seats.items()]

        # fill in opponents in case we want to deconflict later
        for _, player_name in table.seats.items():
            player_data_map[player_name].r1_opponents = [x for x in player_name_list if x != player_name]


    # For now let's go forward with no deconfliction, we just reshuffle and re-assign and if there are dupe opponents so be it
    # print("Round 1 summary : ")
    # for t in r1_tables:
        # print(f"{t.table_number:2} = won by {t.winner_name:9} :: {t.seats} ")

    r2_tables_okay = False
    r2_pairing_count = 0
    while not r2_tables_okay:
        r2_pairing_count += 1
        random.shuffle(PLAYER_NAMES)

        r2_tables = []
        for tablenum in range(1,13):
            table_temp = TournamentTable(tablenum, 2)
            r2_tables.append(table_temp)

        r2_tables_okay = True


        for index, player in enumerate(PLAYER_NAMES):
            play_obj = player_data_map[player]
            desired_draft_slot = play_obj.r2_draft_slot
            tables_with_draft_slot = [t for t in r2_tables if t.seats[desired_draft_slot] is None]

            prev_opts = play_obj.r1_opponents
            filtered_tables = [t for t in tables_with_draft_slot if not len([x for x in prev_opts if x in list(t.seats.values())])]

            if filtered_tables:
                table = filtered_tables[0]
                # fill in stuff
                table.seats[desired_draft_slot] = player
                player_data_map[player].r2_table_num = table.table_number
            else:
                # print(f"Whoopsiedoodle how did this happen {player:9}, {desired_draft_slot}")
                r2_tables_okay = False
                continue


        for t in r2_tables:
            for player in [t for t in t.seats.values() if t is not None]:
                if player not in player_data_map:
                    print("How did you get here Mr ", player)
                r1_opts = player_data_map[player].r1_opponents
                if len([x for x in r1_opts if x in t.seats.values() and x != player]):
                    r2_tables_okay = False
                    continue
                    # print(f"Found a bad r2!! {player} : {r1_opts} ::: {table_players} !! {[x for x in r1_opts if x in table_players and x != player]}")

    
    # print(f"Took {r2_pairing_count} tries for a clean r2")
    if r2_pairing_count not in  r2_algo_efficiency:
        r2_algo_efficiency[r2_pairing_count] = 1
    else:
        r2_algo_efficiency[r2_pairing_count] += 1
    # determine r2 winners!
    for t in r2_tables:
        winning_slot = random.sample(sorted(t.seats.keys()), 1)
        t.winner_name = t.seats[winning_slot[0]]
        if t.winner_name is None:
            print("Got a none winner with left beef: ", t.__dict__)
        player_data_map[t.winner_name].r2_win = True


    # print("Round 2 summary : ")
    # for t in r2_tables:
    #     print(f"{t.table_number:2} = won by {t.winner_name:9} :: {t.seats} ")

    # find double winners
    double_winners = [x for _, x in player_data_map.items() if x.r1_win and x.r2_win]
    # print("Double winners: ", [x.name for x in double_winners])

    double_winner_count = len(double_winners)
    return double_winner_count


result_bucket = {}

iteration_count = 100_000
for _ in tqdm(range(iteration_count)):
    double_win_count = simulate_tournament()
    if double_win_count not in result_bucket:
        result_bucket[double_win_count] = 1
    else:
        result_bucket[double_win_count] += 1


print(f"Ran shuffle simulation for {iteration_count} simulated tournaments")
print("Number of simulations with N double-winners : ")
for x in range(sorted(result_bucket.keys())[-1]):
    if x in result_bucket:
        print(f"{x:2} : {result_bucket[x]:6} :: {(result_bucket[x] / iteration_count)*100:.2f}%")

print("\n**********\nRound 2 pairing algorithim efficiency")
for x in range(sorted(r2_algo_efficiency.keys())[-1]):
    if x in r2_algo_efficiency : 
        print(f"{x:2} : {r2_algo_efficiency[x]:6} :: {(r2_algo_efficiency[x] / iteration_count)*100:.2f}%")