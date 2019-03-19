import json
import attr
import pkg_resources
from collections import defaultdict
from enum import Enum

class EventId(Enum):
    player_wins = -601
    ante = -804
    reveal = -812
    discard = -815
    deal_damage = -902
    apply_damage_dealt = -905
    soak_damage = -906
    concede = -924
    pair_options = -1200
    ante_options = -1201

    @classmethod
    def read(cls, value):
        try:
            return EventId(value)
        except ValueError:
            return value

@attr.s
class GameEventData:
    event_id = attr.ib(converter=int)
    attr_index = attr.ib(converter=int)
    game_state_query = attr.ib(converter=lambda v: REPO.game_state_query[int(v)])
    param_4 = attr.ib(converter=int)
    param_5 = attr.ib(converter=int)
    attr_description = attr.ib()

@attr.s
class GameStateQuery:
    id = attr.ib(converter=int)
    name = attr.ib()
    description = attr.ib()
    param_3 = attr.ib(converter=int)
    func = attr.ib()
    param_name = attr.ib()
    param_6 = attr.ib(converter=int)
    param_7 = attr.ib()
    param_8 = attr.ib(converter=int)


@attr.s
class Fighter:
    id = attr.ib(converter=int)
    name = attr.ib()
    full_name = attr.ib()
    param_3 = attr.ib(converter=int)
    param_4 = attr.ib(converter=int)
    description = attr.ib()
    param_6 = attr.ib(converter=int)
    param_7 = attr.ib(converter=int)
    param_8 = attr.ib(converter=int)
    param_9 = attr.ib(converter=lambda v: int(v) if v is not None else None)
    param_10 = attr.ib(converter=int)
    param_11 = attr.ib(converter=lambda v: int(v) if v is not None else None)
    param_12 = attr.ib(converter=int)
    param_13 = attr.ib(converter=int)


class BCORepo:
    def __init__(self, repo_file):
        self.data = json.load(repo_file)

        self.game_state_query = {
            query.id: query
            for query
            in (GameStateQuery(*row) for row in self.data['repo']['gamestatequery'])
        }
        self.fighter = {
            fighter.id: fighter
            for fighter
            in (Fighter(*row) for row in self.data['repo']['fighter'])
        }

        self._game_event_data = None

    @property
    def game_event_data(self):
        if self._game_event_data is None:
            self._game_event_data = defaultdict(dict)
            for row in self.data['repo']['gameeventdata']:
                self._game_event_data[EventId.read(int(row[0]))][int(row[1])] = GameEventData(*row)
        return self._game_event_data

REPO = BCORepo(pkg_resources.resource_stream('bacon_replay_analyzer', 'var/bco-analyzer/bco_repo.json'))
