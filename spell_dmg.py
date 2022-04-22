"""
Usage:
    .\spell_dmg.bat DEX -dc 15 --dmg 13 17 --bless
    .\spell_dmg.bat WIS -dc 17 --dmg 2 --evade
"""

from dataclasses import dataclass
from math import floor
from random import randint
from argparse import ArgumentParser
from pathlib import Path
import yaml

STR_IND = 0
DEX_IND = 1
CON_IND = 2
INT_IND = 3
WIS_IND = 4
CHA_IND = 5
STAT_ID_BY_NAME = {
    'STR':STR_IND,
    'DEX':DEX_IND,
    'CON':CON_IND,
    'INT':INT_IND,
    'WIS':WIS_IND,
    'CHA':CHA_IND,
}
SPACER = '   '
YAML_FILENAME = 'monsters.yaml'
TRUE_VALUES = (True, 'TRUE', 'True', 'true', 1)

def mod_from_start(stat):
    return floor( (stat - 10)/2 )


def roll(d):
    return randint(1, d)


def roll_n(n,d):
    r = 0
    for i in range(n):
        r += roll(d)
    return r


class Creature:
    def __init__(self, name, stats, bless=False, bane=False):
        self.name = name
        self.stats = stats
        self.mods = [mod_from_start(s) for s in self.stats]
        self.bless = bless
        self.bane = bane

        self.dmg = None
        self.factors = None
        self.total_dmg = None

    def get_stat(self, stat):
        return self.stats[STAT_ID_BY_NAME[stat]]

    def get_mod(self, stat):
        index = STAT_ID_BY_NAME[stat]
        return self.mods[index]

    def make_saves(self, stat, dc, dmg, success, bless=False, bane=False):
        self.rolls = []
        for d in dmg:
            r = roll(20) + self.get_mod(stat)
            if bless or (self.bless in TRUE_VALUES):
                r += roll(4)
            if bless or (self.bane in TRUE_VALUES):
                r -= roll(4)
            self.rolls.append(r)

        self.factors = []
        for r in self.rolls:
            if r > dc:
                self.factors.append(success)
            else:
                # take the full damage
                self.factors.append(1)

        self.total_dmg = 0
        for f, d in zip(self.factors, dmg):
            self.total_dmg += floor(f*d)


def main(args):
    args.dmg = [int(d) for d in args.dmg]

    yaml_path = Path(__file__).parent / YAML_FILENAME
    yaml_data = yaml.load(yaml_path.read_text(), yaml.SafeLoader)

    monsters = []
    for m in yaml_data:
        monsters.append(Creature(m['name'], 
                                 m['stats'], 
                                 m['bless'], 
                                 m['bane']))

    for m in monsters:
        m.make_saves(
            args.stat, 
            args.dc, 
            args.dmg, 
            args.success_factor, 
            args.bless,
            args.bane
        )

    dmg_len       = max([len(str(d)) for d in args.dmg])
    dmg_len       = max(dmg_len, 3)
    name_len      = max([len(m.name) for m in monsters])
    total_dmg_len = max([len(str(m.total_dmg)) for m in monsters])

    line = f'{"":>{name_len}}{SPACER}{"":>{total_dmg_len}}'
    for d in args.dmg:
        line += f'{SPACER}{d:>{dmg_len}}'
    print(line)

    for m in monsters:
        line = f'{m.name:<{name_len}}'
        line += f'{SPACER}{m.total_dmg:>{total_dmg_len}}'
        for f in m.rolls:
            line += f'{SPACER}{f:>{dmg_len}}'
        print(line)


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument(
        'stat',
        default='DEX',
        help='stat used for the save',
    )
    parser.add_argument(
        '-dc',
        default=10,
        type=int,
        help='difficulty class, assumed to be the same for all',
    )
    parser.add_argument(
        '--dmg',
        '--damage',
        nargs='+',
        help='space-delimited damage amounts',
    )
    parser.add_argument(
        '-e', '--evade',
        dest='success_factor',
        action='store_const',
        const=0.0,
        default=0.5,
        help='enemies evade (0 dmg) on save, else half dmg',
    )
    parser.add_argument(
        '-b', '--bless',
        action='store_true',
        help='enemies have bless (or equivalent)',
    )
    parser.add_argument(
        '-n', '--bane',
        action='store_true',
        help='enemies have bane',
    )
    args = parser.parse_args()
    main(args)
