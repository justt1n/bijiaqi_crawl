import re

def extract_integers_from_string(s):
    return [int(num) for num in re.findall(r'\d+', s)]


class Payload:
    def __init__(self, data):
        self.check = data[0]
        self.name = data[1]
        self.id = data[2]
        self.types = data[3].split(",")
        self.gd_min = int(data[4])
        self.gd_max = int(data[5])
        self.sheet_row = data[-1]

    def get(self):
        return self.data


class Result:
    def __init__(self, username, money, min_gold, max_gold, dept, time, link, type, filter):
        self.username = username
        self.money = money
        self.min_gold = min_gold
        self.max_gold = max_gold
        self.dept = dept
        self.time = time
        self.link = link
        self.type = type
        self.filter = filter

    def __init__(self, data):
        self.username = data[0]
        self.money = data[1]
        gold = extract_integers_from_string(data[2])
        if len(gold) != 2:
            self.min_gold = 0
            self.max_gold = 0
        else:
            self.min_gold = gold[0]
            self.max_gold = gold[1]
        self.dept = data[3]
        self.time = data[4]
        self.link = data[5]
        self.type = data[6]
        self.filter = data[7]

    def toArray(self):
        return [self.username, self.money, self.min_gold, self.max_gold, self.dept, self.time, self.link, self.type]

    def get(self):
        return self.username, self.money, self.gold, self.dept, self.time, self.link, self.type, self.filter