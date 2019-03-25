import json
import sys
from configparser import ConfigParser
from enum import Enum
from collections import defaultdict
from pprint import pprint
from .bco_repo import REPO, EventId
import os
from datetime import datetime


class BaseEvent:
    KNOWN_FIELDS = {
    }
    FIRST_DATA_FIELD = 0

    def __init__(self, index, *fields):
        self.index = index
        self.fields = fields

    @property
    def described_fields(self):
        event_data = REPO.game_event_data.get(self.event_type_id, {})
        for idx, value in enumerate(self.fields):
            data_field_idx = idx - self.FIRST_DATA_FIELD + 1
            if idx in self.KNOWN_FIELDS:
                yield (self.KNOWN_FIELDS[idx], getattr(self, self.KNOWN_FIELDS[idx], self.fields[idx][0]))
            elif (data_field_idx) in event_data:
                yield (event_data[data_field_idx].attr_description, value)
            else:
                yield ('UNKNOWN', value)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.index}, {self.event_type_id}, {self.previous_index}, *{self.fields})"

class Event(BaseEvent):
    KNOWN_FIELDS = {
        0: 'event_type_id',
        1: 'previous_index',
    }
    FIRST_DATA_FIELD = 2

    @property
    def event_type_id(self):
        try:
            return EventId(self.fields[0][0])
        except ValueError:
            return self.fields[0][0]


class Setup(BaseEvent):
    KNOWN_FIELDS = {
        2: 'player_0_fighter',
        4: 'player_0_name',
        10: 'player_1_fighter',
        12: 'player_1_name',
    }

    @property
    def player_0_name(self):
        return self.fields[4][0]

    @property
    def player_0_fighter(self):
        return REPO.fighter[self.fields[2][0]]

    @property
    def player_1_name(self):
        return self.fields[12][0]

    @property
    def player_1_fighter(self):
        return REPO.fighter[self.fields[10][0]]

    def __init__(self, index, *fields):
        self.event_type_id = 'GAME_SETUP'
        super(Setup, self).__init__(index, *fields)

EVENT_TYPES = defaultdict(lambda: Event, {
    # EventId.reveal: Reveal,
    # EventId.ante: Ante,
    # EventId.ante_options: AnteOptions,
    # EventId.pair_options: PairOptions,
    # EventId.discard: Discard
})


class Replay:
    def __init__(self, filename):
        self.filename = filename
        self.parsed = ConfigParser()
        self.parsed.read([filename])

    @property
    def name(self):
        return os.path.basename(self.filename)

    @property
    def match_date(self):
        stat = os.stat(self.filename)
        return datetime.fromtimestamp(stat.st_mtime)

    @property
    def player_0(self):
        setup = next(self.parsed_tuples)
        assert setup.event_type_id == 'GAME_SETUP'
        return setup.player_0_name

    @property
    def player_1(self):
        setup = next(self.parsed_tuples)
        assert setup.event_type_id == 'GAME_SETUP'
        return setup.player_1_name

    @property
    def fighter_0(self):
        setup = next(self.parsed_tuples)
        assert setup.event_type_id == 'GAME_SETUP'
        return setup.player_0_fighter

    @property
    def fighter_1(self):
        setup = next(self.parsed_tuples)
        assert setup.event_type_id == 'GAME_SETUP'
        return setup.player_1_fighter

    @property
    def winner(self):
        events = list(self.parsed_tuples)
        end_events = (event for event in events if event.event_type_id in (EventId.player_wins, EventId.concede))

        def _winner(event):
            if event.event_type_id == EventId.player_wins:
                winning_index = event.fields[2][0]
            elif event.event_type_id == EventId.concede:
                winning_index = 1 - event.fields[2][0]
            return getattr(self, f'player_{winning_index}')

        winners = set(_winner(event) for event in end_events if len(event.fields) >= 3)

        assert len(winners) <= 1, f"Unexpectedly more than one winner in {self.name}"
        if len(winners) == 1:
            return winners.pop()
        else:
            return None

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
        section_indexes = sorted(
            (section for section in self.parsed.sections() if section not in ('SIZE', 'GAME_SETUP')),
            key=int
        )
        for section in section_indexes:
            yield (int(section), self.raw_tuple(section))

    def parsed_tuple(self, index, raw_tuple):
        if index == 'SETUP':
            return Setup(index, *raw_tuple)
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
