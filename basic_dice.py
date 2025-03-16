import random


result_bucket = {}
iteration_count = 1_000_000

for _ in range(iteration_count):
    # 72 chances at two 6's
    success_count = 0
    total_count = 0

    players = list(range(73))
    r1_winners = random.sample(players,k=12)
    r2_winners = random.sample(players, k=12)
    # random.shuffle(players)
    # r1_winners = players[0:13]
    # random.shuffle(players)
    # r2_winners = players[0:13]

    double_winners = [x for x in r1_winners if x in r2_winners]

    success_count = len(double_winners)

    # print(f"{success_count} / {total_count}")
    if success_count not in result_bucket:
        result_bucket[success_count] = 1
    else:
        result_bucket[success_count] += 1

print(f"Ran shuffle simulation for {iteration_count} simulated tournaments")
print("Final results : ")
for x in range(len(result_bucket)):
    print(f"{x:2} : {result_bucket[x]:6} :: {(result_bucket[x] / iteration_count)*100:.2f}%")
