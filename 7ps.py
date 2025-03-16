import random
from tqdm import tqdm
import concurrent.futures
from collections import Counter

r2_algo_efficiency  = {}


INVERSE_DRAFT_MAPPING = { 0:5, 1:4, 2:3, 3:2, 4:1, 5:0}

# SOS_FORMAT = "ONLY_GAME_WIN_SCORES"
# SOS_FORMAT = "ALL_OPPONENTS_SCORES"
# SOS_FORMAT = "ONLY_GAME_WIN_GAME_POINTS"
PROBABLISTIC_RD2 = False

class PlayerData:
    name: str = ""
    r1_table_num: int = 0
    r1_draft_slot: int = 0
    r1_opponents: list[str] = []
    r1_win : bool = False
    r1_points : int = 0

    r2_table_num: int = 0
    r2_draft_slot: int = 0
    r2_opponents: list[str] = []
    r2_win: bool = False
    r2_points : int = 0

    opp_totals: int = 0
    win_count: int = 0

    def __init__(self, name: str):
        self.name = name
        self.r1_table_num = -1
        self.r1_draft_slot = -1
        self.r1_opponents = []
        self.r1_win = False
        self.r1_fiesta = False

        self.r2_table_num = -1
        self.r2_draft_slot = -1
        self.r2_opponents = []
        self.r2_win = False
        self.r2_fiesta = False

        self.opp_totals = 0
        self.win_count = 0


class TournamentTable:
    def __init__(self, table_number: int, round: int):
        self.table_number = table_number
        self.round = round
        self.seats = {}
        self.winner_name = ""
        for x in range(6):
            self.seats[x] = None

def simulate_tournament(iter_count: int = 0):

    
    PLAYER_NAMES = [ f"Player {x}" for x in range(1,73)]


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
        player_data_map[winner].r1_points = 10
        if random.randint(0,5) == 0:
            player_data_map[winner].r1_fiesta = True


        player_name_list = [x for _, x in table.seats.items()]

        # fill in opponents in case we want to deconflict later
        for _, player_name in table.seats.items():
            if player_name != winner:
                player_data_map[player_name].r1_points = random.randint(6,10)
            player_data_map[player_name].r1_opponents = [x for x in player_name_list if x != player_name]


    # For now let's go forward with no deconfliction, we just reshuffle and re-assign and if there are dupe opponents so be it
    # print("Round 1 summary : ")
    # for t in r1_tables:
        # print(f"{t.table_number:2} = won by {t.winner_name:9} :: {t.seats} ")

    if PROBABLISTIC_RD2:

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
                    r2_tables_okay = False
                    continue

            if r2_tables_okay:
                for t in r2_tables:
                    for player in [t for t in t.seats.values() if t is not None]:
                        if player not in player_data_map:
                            print("How did you get here Mr ", player)
                        r1_opts = player_data_map[player].r1_opponents
                        if len([x for x in r1_opts if x in t.seats.values() and x != player]):
                            r2_tables_okay = False
                            continue

        
        # print(f"Took {r2_pairing_count} tries for a clean r2")
        if r2_pairing_count not in  r2_algo_efficiency:
            r2_algo_efficiency[r2_pairing_count] = 1
        else:
            r2_algo_efficiency[r2_pairing_count] += 1

    else:
        r2_tables = []
        # build the tables
        for tablenum in range(1,13):
            table_temp = TournamentTable(tablenum, 2)
            r2_tables.append(table_temp)

        # assign players to tables
        for pd in player_data_map.values():
            table_index = (pd.r1_table_num + pd.r1_draft_slot) % 12
            # pd.r2_table_num = ((pd.r1_table_num + pd.r1_drafT_slot) % 12) + 1
            pd.r2_table_num = table_index + 1
            r2_tables[table_index].seats[pd.r2_draft_slot] = pd.name

        # second pass to get everyone's opponents added and determine a winner
        for table in r2_tables:
            table_players = list(table.seats.values())
            for player in table_players:
                player_data_map[player].r2_opponents = [x for x in table_players if x != player]
            table.winner_name = random.sample(table_players, 1)
            




    # determine r2 winners!
    for t in r2_tables:
        winning_slot = random.sample(sorted(t.seats.keys()), 1)
        t.winner_name = t.seats[winning_slot[0]]
        if t.winner_name is None:
            print("Got a none winner with left beef: ", t.__dict__)
        player_data_map[t.winner_name].r2_win = True
        player_data_map[t.winner_name].r2_points = 10
        if random.randint(0,5) == 0:
            player_data_map[t.winner_name].r2_fiesta = True
        for player in t.seats.values():
            if player != t.winner_name:
                player_data_map[player].r2_points = random.randint(6,10)

    

    # sweep wins in here to make life easier later
    for pd in player_data_map.values():
        pd.win_count += 1 if pd.r1_win else 0
        pd.win_count += 1 if pd.r2_win else 0

    double_winner_count = len([x for x in player_data_map.values() if x.win_count == 2])

    single_winners = [x for x in player_data_map.values() if x.win_count == 1]


    # Elspeth partial set, don't have step 5 in 
    WON_ROUND_POINT_MULT = 1000
    LOST_ROUND_POINT_MULT = 100
    DRAFT_SLOT_MULT = 1

    # these are additive not multiplicitave
    
    # this triggers in a game won by someone in seat 4-6 in the draft
    BAD_DRAFT_SEAT_POINT_MOD = 10
    # this currently triggers 5/6th of the time
    FIESTA_PENALTY = 10_000



    # Tally up points from win and lost rounds using multipliers above
    for pd in player_data_map.values():
        # Check for r1 winners
        if pd.r1_win:
            if not pd.r1_fiesta:
                pd.opp_totals += FIESTA_PENALTY
            pd.opp_totals += DRAFT_SLOT_MULT * pd.r1_draft_slot
            for opp in pd.r1_opponents:
                pd.opp_totals += WON_ROUND_POINT_MULT * player_data_map[opp].win_count
        else:
            for opp in pd.r1_opponents:
                pd.opp_totals += LOST_ROUND_POINT_MULT * player_data_map[opp].win_count

        if pd.r2_win:
            if not pd.r2_fiesta:
                pd.opp_totals += FIESTA_PENALTY
            pd.opp_totals += DRAFT_SLOT_MULT * pd.r2_draft_slot
            for opp in pd.r2_opponents:
                pd.opp_totals += WON_ROUND_POINT_MULT * player_data_map[opp].win_count            
        else:
            for opp in pd.r2_opponents:
                pd.opp_totals += LOST_ROUND_POINT_MULT * player_data_map[opp].win_count




    # Add weighting for lower draft seats
    for pd in player_data_map.values():
        if pd.r1_win and pd.r1_draft_slot > 2:
            pd.opp_totals += BAD_DRAFT_SEAT_POINT_MOD
        if pd.r2_win and pd.r2_draft_slot > 2:
            pd.opp_totals += BAD_DRAFT_SEAT_POINT_MOD



    sos_counts = Counter()
    for pd in single_winners:
        sos_counts[pd.opp_totals] += 1


    price_is_right_count = double_winner_count
    overshoot_count = -1
    sos_values = sorted(sos_counts, reverse=True)
    # print(f"db{double_winner_count}+[", end='')
    # for sos_value in sos_values:


    if double_winner_count >= 6:
        return (double_winner_count, double_winner_count, double_winner_count, (-1,-2))

    for sos_value in sos_values:
        # print(f"{sos_counts[sos_value]},",end='')
        count_at_sos_value = sos_counts[sos_value]
        if price_is_right_count + count_at_sos_value == 6:
            price_is_right_count = 6
            overshoot_count = 6
            return (double_winner_count, price_is_right_count, overshoot_count, (0,0))
        elif price_is_right_count + count_at_sos_value > 6:
            overshoot_count = price_is_right_count + count_at_sos_value
            return (double_winner_count, price_is_right_count, overshoot_count, (6-price_is_right_count,count_at_sos_value))
        else:
            price_is_right_count += count_at_sos_value 
            overshoot_count = price_is_right_count


    # print(f"] => [{price_is_right_count},{overshoot_count}]")

    return (double_winner_count, price_is_right_count, overshoot_count, (-2,-2))


# result_bucket = {}

iteration_count = 100_000

with tqdm(total=iteration_count) as pbar:
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = {executor.submit(simulate_tournament, arg): arg for arg in range(iteration_count)}
        results = {}
        for future in concurrent.futures.as_completed(futures):
            arg = futures[future]
            results[arg] = future.result()
            pbar.update(1)
two_oh_bucket = Counter()
num_one_oh_players = Counter()

pir_counter = Counter()
overshoot_counter = Counter()

overshoot_width = Counter()


for result in results.values():
    # print("result",result)
    two_oh = result[0]
    two_oh_bucket[two_oh] += 1
    num_one_oh_players[24 - (2*result[0])] += 1
    pir_counter[result[1]] += 1
    overshoot_counter[result[2]] += 1
    overshoot_width[result[3]] += 1


    

# print(two_oh_bucket)
# print(clean_cut_count_bucket)

# This works w/o parallelism
# for _ in tqdm(range(iteration_count)):
#     double_win_count = simulate_tournament()
#     if double_win_count not in result_bucket:
#         result_bucket[double_win_count] = 1
#     else:
#         result_bucket[double_win_count] += 1

def print_counter_descending_keys(values, int_keys=True):
    if int_keys:
        for x in sorted(range(sorted(values)[-1]), reverse=True):
            if x in values:
                print(f"{x:2} : {values[x]:6} :: {(values[x] / iteration_count)*100:2.2f}%")
    else:
        for x in sorted(values, reverse=True):
            print(f"{x} : {values[x]:6} :: {(values[x] / iteration_count)*100:2.2f}%")

print(f"Ran shuffle simulation for {iteration_count} simulated tournaments")
print("Number of simulations with N double-winners : ")
print_counter_descending_keys(two_oh_bucket)
# for x in range(sorted(two_oh_bucket.keys())[-1]):
#     if x in two_oh_bucket:
#         print(f"{x:2} : {two_oh_bucket[x]:6} :: {(two_oh_bucket[x] / iteration_count)*100:.2f}%")


print("Number of simulations with N SoS - price is right rules : ")
print_counter_descending_keys(pir_counter)
# for x in range(sorted(clean_cut_count_bucket.keys())[-1]):
#     if x in clean_cut_count_bucket:
#         print(f"{x:2} : {clean_cut_count_bucket[x]:6} :: {(clean_cut_count_bucket[x] / iteration_count)*100:.2f}%")

# print("Number of 1-0 players")
# print_counter_descending_keys(num_one_oh_players)
# for x in sorted(num_one_oh_players, reverse=True):
#     print(f"{x:2} :: {num_one_oh_players[x]:6} :: {(num_one_oh_players[x] / iteration_count)*100:.2f}%")

print("Number of players cutting to have at least 6p")
print_counter_descending_keys(overshoot_counter)

print("Number of players in the overshoot group")
print_counter_descending_keys(overshoot_width, int_keys=False)

# print("Trying to measure stratification")
# print_counter_descending_keys(pir_overshoot_count, int_keys = False)
# print(overshoot_count)
# print("\n**********\nRound 2 pairing algorithim efficiency")
# for x in range(sorted(r2_algo_efficiency.keys())[-1]):
#     if x in r2_algo_efficiency : 
#         print(f"{x:2} : {r2_algo_efficiency[x]:6} :: {(r2_algo_efficiency[x] / iteration_count)*100:.2f}%")