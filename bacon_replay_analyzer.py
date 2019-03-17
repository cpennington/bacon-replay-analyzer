import json
import sys
from configparser import ConfigParser
from enum import Enum

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

@attr.s
class GameEventData:
    event_id = attr.ib(converter=int)
    attr_index = attr.ib(converter=int)
    game_state_query = attr.ib(converter=int)
    index_3 = attr.ib(converter=int)
    index_4 = attr.ib(converter=int)
    index_5 = attr.ib(converter=int)
    attr_description = attr.ib()

@attr.s
class GameStateQuery:


class Replay:
    def __init__(self, filename):
        self.parsed = ConfigParser()
        self.parsed.read([filename])
        print(sorted(int(section) for section in self.parsed.sections() if section not in ('GAME_SETUP', 'SIZE')))

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

    def raw_tuples(self):
        yield self.raw_tuple("GAME_SETUP")
        for index in range(2, int(float(self.parsed['SIZE'].get('size').strip('"')))):
            yield self.raw_tuple(str(index))

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
    for tuple in replay.raw_tuples():
        print(tuple)
