from bacon_replay_analyzer import Replay
import sys
from pprint import pprint

replay = Replay(sys.argv[1])
for tuple_ in replay.parsed_tuples:
    pprint(list(tuple_.described_fields))
