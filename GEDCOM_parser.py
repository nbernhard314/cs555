# Author: Adam Undus
# Description: GEDCOM file parser
# Date:  6/6/19

import sys
from prettytable import PrettyTable
import datetime

validLines = []


def parse(file):
    tags = {
        "INDI": {"indent": 0, "args": 1},
        "NAME": {"indent": 1, "args": 2},
        "SEX": {"indent": 1, "args": 1},
        "BIRT": {"indent": 1, "args": 0},
        "DEAT": {"indent": 1, "args": 0},
        "MARR": {"indent": 1, "args": 0},
        "FAMS": {"indent": 1, "args": 1},
        "FAMC": {"indent": 1, "args": 1},
        "FAM": {"indent": 0, "args": 1},
        "HUSB": {"indent": 1, "args": 1},
        "WIFE": {"indent": 1, "args": 1},
        "CHIL": {"indent": 1, "args": 1},
        "DIV": {"indent": 1, "args": 0},
        "DATE": {"indent": 2, "args": 3},
        "HEAD": {"indent": 0, "args": 0},
        "TRLR": {"indent": 0, "args": 0},
        "NOTE": {"indent": 0, "args": -1},
    }
    # individual template:
    # {
    #     'ID':args,
    #     'NAME' : '',
    #     'SEX':'',
    #     'BIRT':'',
    #     'DEAT':'',
    #     'FAMC':'',
    #     'FAMS':''
    # }
    # Family template:
    # {"ID": '', "MARR": "", "DIV": "", "HUSB": "", "WIFE": "", "CHIL": []}
    with open(file, "r") as inputFile:
        for line in inputFile.readlines():
            if line == "":
                continue
            # print('--> ' + line.strip())
            arr = line.strip().split(" ")
            level = int(arr[0])
            tag = arr[1].upper()
            args = arr[2:]
            valid = "Y"
            if len(arr) > 2:
                if arr[1] == "INDI" or arr[1] == "FAM":
                    valid = "N"
                    println(level, tag, valid, args)
                    continue
                if arr[2] == "INDI" or arr[2] == "FAM":
                    tag = arr[2]
                    args = [arr[1]]
            try:
                expectedIndent = tags[tag]["indent"]
                expectedNumArgs = tags[tag]["args"]
            except KeyError as ke:
                valid = "N"
                # println(level, tag, valid, args)
                continue
            if tag == "NOTE" and level == 0:
                # println(level, tag, valid, args)
                continue
            if expectedIndent == level and expectedNumArgs == len(args):
                # println(level, tag, valid, args)
                validLines.append({"level": level, "tag": tag, "args": args})
                continue
            else:
                valid = "N"
                # println(level, tag, valid, args)
                continue


def getFamInfo():
    currentFam = None
    currentIndi = None
    # individuals = []
    individuals = {}
    # families = []
    families = {}
    for lineNum in range(len(validLines)):
        tag = validLines[lineNum]["tag"]
        level = validLines[lineNum]["level"]
        args = validLines[lineNum]["args"]
        # new individual, all tags below are associated w individuals
        if tag == "DATE":
            continue
        if tag == "INDI":
            args = "".join(args)
            currentIndi = args
            individuals[args] = {
                "NAME": "",
                "SEX": "",
                "BIRT": "",
                "DEAT": "",
                "FAMC": "",
                "FAMS": "",
            }
            continue
        if tag in ["NAME", "SEX", "FAMS", "FAMC"]:
            individuals[currentIndi][tag] = args
            continue
        if tag in ["BIRT", "DEAT"]:
            date = " ".join(validLines[lineNum + 1]["args"])
            individuals[currentIndi][tag] = datetime.datetime.strptime(date, "%d %b %Y")
            continue
        # New family, tags below are associated w families
        if tag == "FAM":
            args = "".join(args)
            currentFam = args
            families[args] = {"MARR": "", "DIV": "", "HUSB": "", "WIFE": "", "CHIL": []}
            continue
        if tag == "MARR" or tag == "DIV":
            date = " ".join(validLines[lineNum + 1]["args"])
            families[currentFam][tag] = datetime.datetime.strptime(date, "%d %b %Y")
            continue
        if tag == "HUSB" or tag == "WIFE":
            families[currentFam][tag] = args
        if tag == "CHIL":
            families[currentFam][tag].append(args)
    printInfo(individuals, families)


def printInfo(individuals, families):
    # individuals = sorted(individuals, key=lambda i: i["ID"])
    # families = sorted(families, key=lambda i: i["ID"])
    # Individuals
    table1 = PrettyTable()
    table1.field_names = [
        "ID",
        "Name",
        "Gender",
        "Birthday",
        "Age",
        "Alive",
        "Death",
        "Child",
        "Spouse",
    ]
    for indi in individuals:
        today = datetime.date.today()
        born = individuals[indi]["BIRT"]
        age = (
            today.year - born.year - ((today.month, today.day) < (born.month, born.day))
        )
        alive = False
        if individuals[indi]["DEAT"] == "":
            alive = True
        else:
            age = (
                individuals[indi]["DEAT"].year
                - born.year
                - (
                    (individuals[indi]["DEAT"].month, individuals[indi]["DEAT"].day)
                    < (born.month, born.day)
                )
            )
            individuals[indi]["DEAT"] = individuals[indi]["DEAT"].strftime("%Y-%m-%d")
        table1.add_row(
            [
                indi,
                " ".join(individuals[indi]["NAME"]),
                " ".join(individuals[indi]["SEX"]),
                individuals[indi]["BIRT"].strftime("%Y-%m-%d"),
                age,
                alive,
                individuals[indi]["DEAT"],
                " ".join(individuals[indi]["FAMC"]),
                " ".join(individuals[indi]["FAMS"]),
            ]
        )
    # families
    table2 = PrettyTable()
    table2.field_names = [
        "ID",
        "Married",
        "Divorced",
        "Husband ID",
        "Husband Name",
        "Wife ID",
        "Wife Name",
        "Children",
    ]

    for fam in families:
        if families[fam]["DIV"] == "":
            families[fam]["DIV"] = "N/A"
        else:
            families[fam]["DIV"] = families[fam]["DIV"].strftime("%Y-%m-%d")
        # TODO: Fix these try excepts
        try:
            husband = individuals["".join(families[fam]["HUSB"])]["NAME"]
        except KeyError as ke:
            husband = "Husband not found."
        try:
            wife = individuals["".join(families[fam]["WIFE"])]["NAME"]
        except KeyError as ke:
            wife = "Wife not Found"
        table2.add_row(
            [
                fam,
                families[fam]["MARR"].strftime("%Y-%m-%d"),
                families[fam]["DIV"],
                " ".join(families[fam]["HUSB"]),
                " ".join(husband),
                " ".join(families[fam]["WIFE"]),
                " ".join(wife),
                families[fam]["CHIL"],
            ]
        )
    print("Individuals")
    print(table1)
    print("\nFamilies")
    print(table2)


if __name__ == "__main__":
    # if len(sys.argv) != 2:
    #     print("Usage: GEDCOM_parser_info.py <file>")
    #     exit(1)
    # else:
    #     file = sys.argv[1]
    parse("testGEDCOM.ged")
    getFamInfo()

