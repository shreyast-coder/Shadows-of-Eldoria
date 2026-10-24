"""
SHADOWS OF ELDORIA
A single_file, text-based open-world RPG.
Python 3.9+
No third-party packages required.

Run:
    python shadows_of_eldoria.py

Features:
-Explore a procedurally connceted world
=Turn-based combat, enemy variety, bosses
-Weapons, armor, potions, invntory and equipment
-Quests, shops, gathering, crafting and random events
-Character levels, skills, achievements and journal*
-Save/load to a local JSON file
"""

from __future__ import annotations

import json
import os
import random
import textwrap
import time
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple

GAME_TITLE = "SHADOWS OF ELDORIA"
SAVE_FILE = "eldoria_save.json"
VERSION = "1.0"


#................................................................................
#Console helpers
#................................................................................

def line(char: str = "=", width: int = 72)-> None:
    print(char * width)


def title(text:str):
    line("=")
    print(text.center(72))
    line("=")


def subtitle(text: str) -> None:
    print()
    line("-")
    print(text)
    line("-")


def pause() -> None:
    input("\nPress Enter to continue...")


def say(text: str, width: int = 70) -> None:
    print(textwrap.fill(str(text), width=width))


def ask(prompt: str) -> str:
    return input(prompt).strip()


def ask_int(prompt: str, low: int, high: int) -> int:
    while True:
        raw = ask(prompt)
        try:
            value = int(raw)
        except ValueError:
            print(f"Enter a number from {low} to {high}.")
            continue
        if low <= value <= high:
            return value
        print(f"Choose a number from {low} to {high}.")


def yes_no(promt: str, default: bool = True) -> bool:
    suffix = "[Y/n]" if default else "[y/N]"
    while True:
        answer = ask(f"{promt} {suffix} ").lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer yes or no.")


def clear_screen() -> None:
    #Avoid shell commands so the game remains portable.
    print("\n" * 2)


def bar(value: int, maximum: int, size: int = 20) -> str:
    maximum = max(1, maximum)
    value = max(0, min(value, maximum))
    filled = round(size * value / maximum)
    return "[" + "#" * filled + "-" * (size - filled) + "]"


def slow_print(text: str, delay: float = 0.012) -> None:
    #Short dramatic text effect. Set delay to Zero for instant output.
    for char in text:
        print(char, end="", flush=True)
        if delay:
            time.sleep(delay)
    print()


#................................................................................
#Data models
#................................................................................

@dataclass
class Item:
    name: str
    kind: str
    description: str
    value: int = 0
    power: int = 0
    weight: float = 1.0
    rarity: str = "Common"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Item":
        return cls(**data)


@dataclass
class EnemyTemplete:
    name: str
    hp: int
    attack: int
    defense: int
    xp: int
    gold: int
    description: str
    boss: bool = False
    special: str = ""


@dataclass
class Quest:
    key: str
    name: str
    description: str
    goal_type: str
    target: str
    required: int
    reward_gold: int
    reward_xp: int
    reward_item: str = ""
    progress: int = 0
    complete: bool = False
    claimed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        return cls(**data)


#................................................................................
# Item Catalogue
#................................................................................

ITEMS: Dict[str, Item] = {
    "Small Potion": Item("Small Potion", "consumable", "Restores 25 health.", 12, 25, 0.3),
    "Healing Potion": Item(
        "Healing Potion", "consumable",
        "Restores 45 health.", 20, 45, 0.3
    ),
    "Large Potion": Item("Large Potion", "consumable", "Restores 60 health.", 30, 60, 0.4, "Uncommon"),
    "Greater Potion": Item("Greater Potion", "consumable", "Restores 120 health.", 75, 120, 0.5, "Rare"),
    "Energy Tonic": Item("Energy Tonic", "consumable", "Restores 25 energy.", 22, 25, 0.3),
    "Antitode": Item("Antitode", "consumable", "Cures Posion.", 15, 0, 0.2),
    "Wooden Sword": Item("Wooden Sword", "weapon", "A training blade.", 10, 3, 2.0),
    "Iron Sword": Item("Iron Sword", "weapon", "A dependable iron sword.", 65, 8, 3.0, "Uncommon"),
    "Steel Sword": Item("Steel Sword", "weapon", "A finely balanced steel sword.", 150, 14, 3.5, "Rare"),
    "Knightblade": Item("Knightblade", "weapon", "A blade forged for a royal guard.", 320, 22, 4.0, "Epic"),
    "Moonfang": Item("Moonfang", "weapon", "A legendary sword that glows at night.", 800, 32, 3.0, "Legendary"),
    "Oak Staff": Item("Oak Staff", "weapon", "A staff that helps focus energy.", 45, 5, 2.0, "Uncommon"),
    "Apprentice Wand": Item("Apprentice Wand", "weapon", "A small magical wand.", 90, 7, 1.0, "Uncommon"),
    "Hunter Bow": Item("Hunter Bow", "weapon", "A sturdy bow for the wilds.", 100, 9, 2.0, "Uncommon"),
    "Leather Armor": Item("Leather Armor", "armor", "Light armor made from cured hide", 45, 3, 3.0),
    "Chainmail": Item("Chainmail", "armor", "Linked mi=etal rings protect the body.", 120, 7, 6.0, "Uncommon"),
    "Knight Armor": Item("Knight Armor", "armor", "Heavy armor worn by royal knights.", 280, 12, 8.0, "Rare"),
    "Dragon Scale": Item("Dragon Scale", "armor", "Armor crafted from Ancient scales.", 700, 18, 5.0, "Legendary"),
    "Wolf Pelt": Item("Wolf Pelt", "material", "A warm pelt useful for crafting.", 14, 0, 1.0),
    "Herb": Item("Herb", "material", "A fragrant medicinal plant.", 5, 0, 0.2),
    "Iron Ore": Item("Iron Ore", "material", "Ore that can be smelted.", 8, 0, 2.0),
    "Crystal Shard": Item("Crystal Shard", "material", "A shard humming with magic.", 25, 0, 0.2, "Uncommon"),
    "Ancient Relic": Item("Ancient Relic", "quest", "An object from a forgptter age.", 100, 0, 1.0, "Rare"),
    "Goblin Ear": Item("Goblin Ear", "material", "Proof of a goblin hunt.", 4, 0, 0.1),
    "Spider Silk": Item("Spider Silk", "material", "Strong silk from a cave spider.", 12, 0, 0.1, "Uncommon"),
    "Dragon Heart": Item("Dragon Heart", "quest", "A warm, pulsing magical core.", 500, 0, 1.0, "Legendary"),
    "Fishing Rod": Item("Fishing Rod", "tool", "Useful near rivers and lakes.", 25, 0, 1.5),
    "Pickaxe": Item("Pickaxe", "tool", "Useful for mining ore.", 30, 0 ,2.5),
    "Lucky Charm": Item("Lucky Charm", "accessory", "Slightly improves rewards.", 100, 1, 0.2, "Rare"),
}

SHOP_STOCK = [
    "Small Potion", "Healing Potion", "Energy Tonic", "Antitode",
    "Iron Sword", "Steel Sword", "Oak Staff", "Hunter Bow",
    "Leather Armor", "Chainmail", "Fishing Rod", "Pickaxe",
]

CRAFTING_RECIPES = {
    "Healing Potion": {"Herb": 3},
    "Greater Potion": {"Herb": 5, "Crystal Shard": 1},
    "Iron Sword": {"Iron Ore": 5},
    "Steel Sword": {"Iron Ore": 8, "Crystal Shard": 1},
    "Leather Armor": {"Wolf Pelt": 4},
}


#................................................................................................................
#World Map
#................................................................................................................

# Part 1: Data Models, Catalogues, World Map, Enemies, Quests, and Player Setup

from dataclasses import dataclass, asdict
from typing import Dict, List, Optional

@dataclass
class EnemyTemplate:
    name: str
    hp: int
    attack: int
    defense: int
    xp: int
    gold: int
    description: str
    boss: bool = False
    special: str = ""

@dataclass
class Quest:
    key: str
    name: str
    description: str
    goal_type: str
    target: str
    required: int
    reward_gold: int
    reward_xp: int
    reward_item: str = ""
    progress: int = 0
    complete: bool = False
    claimed: bool = False

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        return cls(**data)

WORLD: Dict[str, dict] = {
    "Oakheart Village": {
        "type": "town",
        "description": "A quiet village surrounded by old oak trees.",
        "neighbors": ["Whispering Woods", "Riverbend", "Sunfield Road"],
        "danger": 0,
        "features": ["shop", "inn", "quest", "craft"],
    },
    "Whispering Woods": {
        "type": "forest",
        "description": "Tall trees sway above mossy paths.",
        "neighbors": ["Oakheart Village", "Moonlit Glade", "Old Watchtower"],
        "danger": 1,
        "features": ["gather", "hunt"],
    },
    "Riverbend": {
        "type": "river",
        "description": "A clear river curves through a grassy valley.",
        "neighbors": ["Oakheart Village", "Misty Marsh", "Sunfield Road"],
        "danger": 1,
        "features": ["fish", "gather"],
    },
    "Sunfield Road": {
        "type": "road",
        "description": "A broad dirt road passes through golden fields.",
        "neighbors": ["Oakheart Village", "Riverbend", "Crossroads", "Bandit Camp"],
        "danger": 1,
        "features": ["travel"],
    },
    "Moonlit Glade": {
        "type": "glade",
        "description": "Silver flowers shine beneath a thick canopy.",
        "neighbors": ["Whispering Woods", "Crystal Cavern"],
        "danger": 2,
        "features": ["gather"],
    },
    "Old Watchtower": {
        "type": "ruins",
        "description": "A broken tower leans over the forest.",
        "neighbors": ["Whispering Woods", "Crossroads"],
        "danger": 2,
        "features": ["explore"],
    },
    "Misty Marsh": {
        "type": "swamp",
        "description": "Cold mist curls over dark water.",
        "neighbors": ["Riverbend", "Sunken Shrine"],
        "danger": 2,
        "features": ["gather", "hunt"],
    },
    "Crossroads":{
        "type": "hub",
        "description": "Four old roads meet beside a weathered statue.",
        "neighbors": ["Sunfield Road", "Old Watchtower", "Stonebridge", "Bandit Camp"],
        "danger": 2,
        "features": ["quest"],
    },
    "Bandit Camp": {
        "type": "camp",
        "description": "Rough tents surround a smoky fire.",
        "neighbors": ["Sunfield Road", "Crossroads", "Ashen Hills"],
        "danger": 3,
        "features": ["explore"],
    },
    "Crystal Cavern": {
        "type": "cave",
        "description": "Blue crystals light a network of caves.",
        "neighbors": ["Moonlit Glade", "Ashen Hills"],
        "danger": 3,
        "features": ["mine", "explore"],
    },
    "Stonebridge": {
        "type": "town",
        "description": "A fortified settlement guards the ravine bridge.",
        "neighbors":["Crossroads", "Royal Highway", "Sunken Shrine"],
        "danger": 0,
"features": ["shop", "inn", "quest", "craft"],
    },
    "Sunken Shrine":{
        "type": "ruins",
        "description": "Ancient pillars rise from shallow water.",
        "neighbors": ["Misty Marsh", "Stonebridge", "Ashen Hills"],
        "danger": 3,
        "features": ["explore"],
    },
    "Ashen Hills": {
        "type": "mountain",
        "description": "Grey slopes climb toward a smokng ridge,",
        "neighbors": ["Bandit Camp", "Crystal Cavern", "Sunken Shrine", "Dragon Pass"],
        "danger": 4,
        "features": ["mine", "hunt"],
    },
    "Royal Highway": {
        "type": "road",
        "description": "A paved highway leads toward the capital.",
        "neighbors": ["Stonebridge", "Capital Gate"],
        "danger": 1,
        "features": ["travel"],
    },
    "Capital Gate": {
        "type": "city",
        "description": "Tall white walls surround the capital.",
        "neighbors": ["Royal Highway", "Royal Capital"],
        "danger": 0,
        "features": ["quest"],
    },
    "Royal Capital": {
        "type": "city",
        "description": "Banners wave about busy streets and the palace.",
        "neighbors": ["Capital Gate"],
        "danger": 0,
        "features": ["shop", "inn", "quest", "craft"], 
    },
    "Dragon Pass": {
        "type": "mountain",
        "description": "A narrow pass cuts black cliffs.",
        "neighbors": ["Ashen Hills", "Dragon's Lair"],
        "danger": 5,
        "features": ["explore"],
    },
    "Dragon's Lair": {
        "type": "boss",
        "description": "A vast cavern opens beneath a volcano.",
        "neighbors": ["Dragon Pass"],
        "danger": 6,
        "features": ["boss"],
    },
}

ENEMIES: Dict[str, EnemyTemplate] = {
    "Forest Slime": EnemyTemplete("Forest Slime", 18, 4, 1, 12, 5, "A wobbling green gel.", special="split"),
    "Wild Wolf": EnemyTemplete("Wild Wolf", 25, 6, 2, 18, 7, "A hungry wolf.", special="bleed"),
    "Goblin Scout": EnemyTemplate("Goblin Scout", 28, 7, 2, 22, 10, "A small raider.", special="steal"),
    "Bandit": EnemyTemplate("Bandit", 38, 9, 3, 30, 16, "A masked outlaw.", special="heavy"),
    "Cave Spider": EnemyTemplate("Cave Spider", 34, 8, 2, 28, 13, "A cave spider.", special="poison"),
    "Marsh Wisp": EnemyTemplate("Marsh Wisp", 30, 10, 1, 32, 15, "A pale floating light.", special="drain"),
    "Stone Guardian": EnemyTemplate("Stone Guardian", 65, 12, 8, 60, 30, "A stone statue.", special="heavy"),
    "Ash Drake": EnemyTemplate("Ash Drake", 82, 15, 5, 85, 45, "A small dragon beast.", special="burn"),
    "Bandit Captain": EnemyTemplate("Bandit Captain", 110, 17, 7, 120, 90, "Camp Leader.", True, "heavy"),
    "Ancient Golem": EnemyTemplate("Ancient Golem", 160, 20, 12, 180, 140, "Runed guardian.", True, "stun"),
    "The Ashen Dragon": EnemyTemplate("The Ashen Dragon", 420, 28, 14, 1000, 1000, "Ancient dragon.", True, "burn"),
}

AREA_ENEMIES = {
    "Whispering Woods": ["Forest Slime", "Wild Wolf", "Goblin Scout"],
    "Riverbend": ["Forest Slime", "Wild Wolf"],
    "Sunfield Road": ["Goblin Scout", "Bandit"],
    "Moonlit Glade": ["Forest Slime", "Marsh Wisp"],
    "Old Watchtower": ["Goblin Scout", "Stone Guardian"],
    "Misty Marsh": ["Marsh Wisp", "Cave Spider"],
    "Crossroads": ["Goblin Scout", "Bandit"],
    "Bandit Camp": ["Bandit", "Goblin Scout", "Bandit Captain"],
    "Crystal Cavern": ["Cave Spider", "Stone Guardian"],
    "Sunken Shrine": ["Marsh Wisp", "Ancient Golem"],
    "Ashen Hills": ["Ash Drake", "Stone Guardian"],
    "Dragon Pass": ["Ash Drake", "Ash Drake"],
    "Dragon's Lair": ["The Ashen Dragon"],
}

QUEST_DEFINITIONS = [
    Quest("herbs", "A Healer's Request", "Collect 5 herbs for the village healer.", "gather", "Herb", 5, 45, 35, "Healing Potion"),
    Quest("goblins", "Trouble on the Road", "Defeat 4 Goblin Scouts.", "kill", "Goblin Scout", 4, 60, 50, "Iron Sword"),
    Quest("wolves", "Wolves at the Edge", "Defeat 3 Wild Wolves.", "kill", "Wild Wolf", 3, 40, 35, "Leather Armor"),
    Quest("relic", "The Lost Relic", "Find an Ancient Relic in the Old Watchtower.", "find", "Ancient Relic", 1, 100, 80, "Crystal Shard"),
    Quest("bandits", "Break the Camp", "Defeat the Bandit Captain.", "kill", "Bandit Captain", 1, 180, 150, "Steel Sword"),
    Quest("crystals", "A Shimmering Problem", "Collect 3 Crystal Shards.", "gather", "Crystal Shard", 3, 90, 80, "Greater Potion"),
    Quest("golem", "The Sleeping Guardian", "Defeat an Ancient Golem.", "kill", "Ancient Golem", 1, 220, 200, "Knightblade"),
    Quest("dragon", "The Ashen Threat", "Defeat the Ashen Dragon in Dragon's Lair.", "kill", "The Ashen Dragon", 1, 1000, 1000, "Moonfang"),
]

class Player:
    def __init__(self, name: str, hero_class: str):
        self.name = name
        self.hero_class = hero_class
        self.level = 1
        self.xp = 0
        self.gold = 40
        self.max_hp = 100
        self.hp = 100
        self.max_energy = 30
        self.energy = 30
        self.base_attack = 7
        self.base_defense = 2
        self.weapon = "Wooden Sword"
        self.armor = ""
        self.accessory = ""
        self.location = "Oakheart Village"
        self.inventory: Dict[str, int] = {"Small Potion": 3, "Herb": 2, "Wooden Sword": 1}
        self.visited = ["Oakheart Village"]
        self.kills: Dict[str, int] = {}
        self.gathered: Dict[str, int] = {}
        self.quests: Dict[str, Quest] = {}
        self.flags: Dict[str, bool] = {}
        self.journal: List[str] = ["You arrived in Oakheart Village."]
        self.achievements: List[str] = []
        self.skill_points = 0
        self.skills: Dict[str, int] = {"Power Strike": 0, "First Aid": 0, "Scavenger": 0}
        self.play_time = 0
        self.steps = 0

    @property
    def weapon_power(self) -> int:
        return ITEMS.get(self.weapon, ITEMS["Wooden Sword"]).power

    @property
    def armor_power(self) -> int:
        return 0

    @property
    def attack(self) -> int:
        return self.base_attack + self.weapon_power + self.level * 2

    @property
    def defense(self) -> int:
        return self.base_defense + self.armor_power + self.level // 3

    def add_item(self, name: str, amount: int = 1) -> None:
        if amount > 0:
            self.inventory[name] = self.inventory.get(name, 0) + amount

    def remove_item(self, name: str, amount: int = 1) -> bool:
        if self.inventory.get(name, 0) < amount:
            return False
        self.inventory[name] -= amount
        if self.inventory[name] <= 0:
            del self.inventory[name]
        return True

    def heal(self, amount: int) -> int:
        old = self.hp
        self.hp = min(self.max_hp, self.hp + amount)
        return self.hp - old

    def gain_xp(self, amount: int) -> None:
        self.xp += amount
        while self.xp >= (60+ (self.level - 1) * 45):
            self.xp -= (60 + (self.level - 1) * 45)
            self.level += 1
            self.max_hp += 12
            self.hp = self.max_hp


    



    def has_item(self, name: str, amount: int = 1) -> bool:
        return self.inventory.get(name, 0) >= amount

    def update_quest_progress(
        self, goal_type: str, target: str, amount: int = 1
    ) -> None:
        for quest in self.quests.values():
            if (
                quest.goal_type == goal_type
                and quest.target == target
                and not quest.complete
            ):
                quest.progress = min(
                    quest.required, quest.progress + amount
                )
                if quest.progress >= quest.required:
                    quest.complete = True
                    print(f"Quest completed: {quest.name}")

    def check_achievements(self) -> None:
        if len(self.visited) >= 5 and "Explorer" not in self.achievements:
            self.achievements.append("Explorer")
            print("Achievement unlocked: Explorer")

    def to_dict(self) -> dict:
        data = self.__dict__.copy()
        data["quests"] = {
            key: quest.to_dict()
            for key, quest in self.quests.items()
        }
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "Player":
        data = data.copy()
        data["quests"] = {
            key: Quest.from_dict(quest)
            for key, quest in data.get("quests", {}).items()
        }
        player = cls(data["name"], data["hero_class"])
        player.__dict__.update(data)
        return player