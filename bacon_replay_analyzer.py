import json
import sys
from configparser import ConfigParser
from enum import Enum
import attr
from collections import defaultdict
from pprint import pprint

# repoFile = open(r"BCO-resource\bco_repo.json", encoding='utf-8')
# #replayTest = open(r"BCO-resource\1eaf872c-e5bc-4d67-a6b7-0150acbc4f0a_replay.bcr", encoding='utf-8')
# replayTest = open(input("Replay file path: "), encoding='utf-8')

class ReadData(Enum):
    readBase0 = 1
    readStyle0 = 2
    readFinisher0 = 3
    readBase1 = 4
    readStyle1 = 5
    readFinisher1 = 6


def show_fighter(event_data, step):
    print()
    if event_data["2_value"][0] == "0":
        print(p0charName, step)
    if event_data["2_value"][0] == "1":
        print(p1charName, step)


def int_temp(event_data, field):
    return int(event_data[field][:event_data[field].find(".")])

class EventId(Enum):
    reveal = -812
    ante = -804
    ante_options = -1201
    pair_options = -1200
    discard = -815

    @classmethod
    def read(cls, value):
        try:
            return EventId(value)
        except ValueError:
            return value

class Event:
    KNOWN_FIELDS = {
        0: 'event_type_id',
        1: 'previous_index',
    }

    def __init__(self, index, *fields):
        self.index = index
        self.fields = fields

    @property
    def event_type_id(self):
        try:
            return EventId(self.fields[0][0])
        except ValueError:
            return self.fields[0][0]

    @property
    def previous_index(self):
        return self.fields[1][0]

    @property
    def described_fields(self):
        event_data = bco_repo.game_event_data.get(self.event_type_id, {})
        for idx, value in enumerate(self.fields):
            if idx in self.KNOWN_FIELDS:
                yield (self.KNOWN_FIELDS[idx], getattr(self, self.KNOWN_FIELDS[idx]))
            elif (idx-1) in event_data:
                yield (event_data[idx-1].attr_description, value)
            else:
                yield ('UNKNOWN', value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.index}, {self.event_type_id}, {self.previous_index}, *{self.fields})"

class Setup(Event):
    pass

EVENT_TYPES = defaultdict(lambda: Event, {
    # EventId.reveal: Reveal,
    # EventId.ante: Ante,
    # EventId.ante_options: AnteOptions,
    # EventId.pair_options: PairOptions,
    # EventId.discard: Discard
})


@attr.s
class GameEventData:
    event_id = attr.ib(converter=int)
    attr_index = attr.ib(converter=int)
    game_state_query = attr.ib(converter=lambda v: bco_repo.game_state_query[int(v)])
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


class BCORepo:
    def __init__(self, repo_file):
        self.data = json.load(repo_file)

        self.game_state_query = {
            int(row[0]): GameStateQuery(*row)
            for row in self.data['repo']['gamestatequery']
        }

        self._game_event_data = None

    @property
    def game_event_data(self):
        if self._game_event_data is None:
            self._game_event_data = defaultdict(dict)
            for row in self.data['repo']['gameeventdata']:
                self._game_event_data[EventId.read(int(row[0]))][int(row[1])] = GameEventData(*row)
        return self._game_event_data

with open('./bco_repo.json') as data_file:
    bco_repo = BCORepo(data_file)


class Replay:
    def __init__(self, filename):
        self.parsed = ConfigParser()
        self.parsed.read([filename])

    def raw_tuple(self, timestamp):
        section = self.parsed[timestamp]
        item_count = int(float(section.get('size').strip('"')))
        return list(
            self.read_value(timestamp, index)
            for index in range(item_count)
        )

    def read_value(self, timestamp, index):
        section = self.parsed[timestamp]
        str_value = section[f'{index}_value'].strip('"')
        read_type = section[f'{index}_read_type'].strip('"')
        type = int(float(section.get(f'{index}_type').strip('"')))
        if read_type == "string":
            return (str_value, type)
        elif read_type == "real":
            return (int(float(str_value)), type)

    @property
    def raw_tuples(self):
        yield ("SETUP", self.raw_tuple("GAME_SETUP"))
        for index in range(2, int(float(self.parsed['SIZE'].get('size').strip('"')))):
            yield (index, self.raw_tuple(str(index)))

    def parsed_tuple(self, index, raw_tuple):
        if index == 'SETUP':
            return Setup(*raw_tuple)
        else:
            try:
                event_type = EventId(raw_tuple[0][0])
            except ValueError:
                event_type = raw_tuple[0][0]
            return EVENT_TYPES[event_type](index, *raw_tuple)

    @property
    def parsed_tuples(self):
        for index, tuple in self.raw_tuples:
            yield self.parsed_tuple(index, tuple)

def parse_replay(filename):
    replayEventDict = {}
    lastevent = 0
    p0char = 0
    p1char = 0
    for line in replayTest:
        if line[0] == "[" and line[-2] == "]":
            try:
                lastevent = int(line[1:-2])
                if lastevent in replayEventDict:
                    print("duplicate event?")
                else:
                    replayEventDict[lastevent] = "{"
            except ValueError:
                lastevent = line[1:-2]
        else:
            if isinstance(lastevent, int):
                eqlidx = line.find("=")
                if eqlidx >= 0:
                    replayEventDict[lastevent] += "\"" + line[0:eqlidx] + "\":" + line[eqlidx + 1:-1] + ",\n"
            if lastevent == "GAME_SETUP":
                if line.find("10_value") == 0:
                    p1char = int(line[line.find("\"") + 1:line.find(".")])
                if line.find("2_value") == 0:
                    p0char = int(line[line.find("\"") + 1:line.find(".")])
    # print(sorted(replayEventDict))
    test = json.loads(repoFile.read())
    elemDict = {}
    for idx in range(len(test["repo"]["source"])):
        elemDict[int(test["repo"]["source"][idx][0])] = test["repo"]["source"][idx][1]
    p1charName = ""
    p0charName = ""
    for idx in range(len(test["repo"]["fighter"])):
        if int(test["repo"]["fighter"][idx][0]) == p1char:
            p1charName = test["repo"]["fighter"][idx][2]
        if int(test["repo"]["fighter"][idx][0]) == p0char:
            p0charName = test["repo"]["fighter"][idx][2]
    print(p0charName + " VS " + p1charName)


    for idx in sorted(replayEventDict):
        temp = json.loads(replayEventDict[idx][:-2] + "}")
        eventID = int_temp(temp, "0_value")
        if eventID == -812:
            show_fighter(temp, "REVEAL")
            if(int_temp(temp, "3_value") == 2):
                styleID = int_temp(temp, "5_value")
                print(styleID,
                    elemDict[styleID])
            else:
                print("FINISHER")
            baseID = int_temp(temp, "4_value")
            print(baseID,
                elemDict[baseID])
        if eventID == -804:
            show_fighter(temp, "ANTE")
            anteID = int_temp(temp, "3_value")
            print(anteID, elemDict[anteID])
        if eventID == -1201:
            show_fighter(temp, "ANTE OPTIONS")
            anteNum = int(temp["3_value"][:temp["3_value"].find(".")])
            for i in range(anteNum):
                anteID = int(temp[str(i+4) + "_value"][:temp[str(i+4) + "_value"].find(".")])
                print(anteID, elemDict[anteID])
        if eventID == -1200:
            print()
            nextNum = 2
            readStep = ReadData(1)
            for i in range(2, int_temp(temp, "size")):
                if i == nextNum:
                    if readStep == ReadData(1):
                        nextNum = i + int_temp(temp, str(i)+"_value")+1
                        print(p0charName, "Bases")
                        readStep = ReadData(readStep.value+1)
                    elif readStep == ReadData(2):
                        nextNum = i + int_temp(temp, str(i)+"_value")+1
                        print(p0charName, "Styles")
                        readStep = ReadData(readStep.value+1)
                    elif readStep == ReadData(3):
                        nextNum = i + int_temp(temp, str(i)+"_value")+1
                        print(p0charName, "Finishers")
                        readStep = ReadData(readStep.value+1)
                    elif readStep == ReadData(4):
                        nextNum = i + int_temp(temp, str(i)+"_value")+1
                        print(p1charName, "Bases")
                        readStep = ReadData(readStep.value+1)
                    elif readStep == ReadData(5):
                        nextNum = i + int_temp(temp, str(i)+"_value")+1
                        print(p1charName, "Styles")
                        readStep = ReadData(readStep.value+1)
                    elif readStep == ReadData(6):
                        nextNum = i + int_temp(temp, str(i)+"_value")+1
                        print(p1charName, "Finishers")
                        #readStep = ReadData(readStep.value+1)
                else:
                    cardId = int_temp(temp, str(i)+"_value")
                    print(cardId, elemDict[cardId])

if __name__ == "__main__":
    replay = Replay(sys.argv[1])
    for tuple in replay.parsed_tuples:
        pprint(list(tuple.described_fields))
