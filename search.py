from __future__ import annotations

import argparse
import itertools
import json
from dataclasses import dataclass
from typing import Dict, List, NamedTuple, Optional, Sequence, Set
import random


@dataclass
class Item:
    """Hold a single item (which may have multiple different sets of data), and its aspects."""
    item: str
    data: Optional[List[str]]
    aspects: Dict[str, int]

    @staticmethod
    def from_raw(name: str, asp: List[str]) -> Item:
        name, _, data = name.partition(" --- ")
        aspects = {split[1]: int(split[0]) for split in map(lambda x: str.split(x, " ", 1), asp)}

        return Item(name, [data] if data else None, aspects)

    def __str__(self) -> str:
        out = f"{self.item!r}\n"
        if self.data is not None:
            out += f"- With data{'s' if self.data is not None and len(self.data) > 1 else ''}: {', '.join(self.data)}\n"

        out += f"- With Aspects: \n"
        out += "\n".join(f"    - {a + ':':<14}{c}" for a, c in self.aspects.items())

        return out


def load_aspects(item_dict: Dict[str, List[str]]) -> List[Item]:
    """
    Parse the output of https://github.com/redcatone/random-minecraft-scripts/tree/master/thaumic-jei into something
    more usable.
    """
    raw = list(map(lambda pair: Item.from_raw(pair[0], pair[1]), item_dict.items()))
    # Dedupe
    out: Dict[str, List[Item]] = {}
    for item in raw:
        if (vl := out.get(item.item)) is not None:
            found = False
            for v in vl:
                if v.aspects != item.aspects:
                    continue

                if v.data is None:
                    v.data = ['None']

                if item.data is None:
                    item.data = ['None']

                v.data += item.data
                found = True
                break

            if not found:
                out[item.item].append(item)
                continue

        else:
            out[item.item] = [item]

    return list(itertools.chain(*out.values()))


def search_aspects(to_find: List[str], items: List[Item], or_find=False, perfect=False) -> List[Item]:
    """
    Search for aspects in the given list.

    If or is provided, search for all items that contain one or more of the items in the list

    : param to_find: The aspects to search for
    : param items: The available items
    : param or_find: Whether or not to treat the to_find list as an OR, defaults to False
    : return: The found items
    """
    searches: List[List[str]] = []
    if or_find:
        searches.extend([x] for x in to_find)
    else:
        searches = [to_find]

    out: List[Item] = []
    for search in searches:
        found = filter(lambda i: all(a in i.aspects for a in search), items)
        if perfect:
            found = filter(lambda i: len(i.aspects) == len(search), found)

        out.extend(filter(lambda x: x not in out, found))

    return list(out)


def list_aspects(items: List[Item]) -> Set[str]:
    """List all possible aspects in the given item list"""
    return set(itertools.chain(*(list(a.aspects.keys()) for a in items)))


def display_item(item: Item, oneline: bool, verbose: bool, targets: List[str]):
    """
    Display an item based on the given rules.

    All rules assumed to be mutually exclusive.
    """
    item_data = f"{ '-- ' + ', '.join(item.data) if item.data else ''}"
    if verbose:
        print(item)
        print()

    elif oneline:
        print(*(f"{a}: {item.aspects[a]}" for a in targets if a in item.aspects), f"{item.item!r} {item_data}")

    else:
        print(f"{item.item!r} {item_data}")
        for s in targets:
            if s in item.aspects:
                print(f"  - {s}: {item.aspects[s]}")

        print()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", "-l", action="store_true", help="List all possible aspects")
    parser.add_argument(
        "--perfect", "-p", action="store_true",
        help="Search for items that ONLY contain the given aspect"
    )

    display = parser.add_mutually_exclusive_group()

    display.add_argument("--verbose", "-v", action="store_true", help="Show all aspects on the returned items")
    display.add_argument("--oneline", action="store_true", help="Display results on one line")
    parser.add_argument(
        "--or-search",
        help="search becomes a list of values to search for individually, rather than all together",
        action="store_true",
    )

    parser.add_argument("search", help="Search for items with all these aspects", nargs="*")

    args = parser.parse_args()
    # args = parser.parse_args("aer bestia --oneline --or-search".split())

    with open("./json_output.json") as f:
        data = f.read()

    aspects = load_aspects(json.loads(data))

    if args.list and len(args.search) > 0:
        print("Cannot list aspects and search for aspects")
        return

    possible_aspects = list(list_aspects(aspects))
    possible_aspects.sort()
    if args.list:
        print(f"Valid aspects are: {', '.join(possible_aspects)}")

    if len(args.search) > 0:
        print("Searching...")
        if (x := set(args.search) - set(possible_aspects)):
            print(f"Warning: Unknown aspects found: {', '.join(x)}, use -l to see available aspects")
        found = search_aspects(args.search, aspects, args.or_search, args.perfect)
        if len(found) == 0:
            print("No items found. Consider broadening your search or removing --perfect")

        for item in found:
            display_item(item, args.oneline, args.verbose, args.search)


if __name__ == "__main__":
    main()
