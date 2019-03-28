from bacon_replay_analyzer import Replay
import sys
from pprint import pprint

replay = Replay(sys.argv[1])
for tuple_ in replay.parsed_tuples:
    pprint(list(tuple_.described_fields))

print(
    "Player 0:",
    replay.player_0,
    "as",
    replay.fighter_0.name,
    ", current record:",
    replay.record_0,
)
print(
    "Player 1:",
    replay.player_1,
    "as",
    replay.fighter_1.name,
    ", current record:",
    replay.record_1,
)
print("Played on:", replay.match_date)
print("Winner: ", replay.winner)
