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




import json
import os
import random
import time
from typing import Optional


class Game:
    def __init__(self) -> None:
        self.player: Optional[Player] = None
        self.running = True
        self.start_time = time.time()

    def start(self) -> None:
        while True:
            title(GAME_TITLE)
            print("A land of ancient ruins, dangerous roads, and forgotten magic.")
            print("Explore, grow stronger, and discover the source of the ash.")
            print()
            print("1. New game")
            print("2. Load game")
            print("3. Help")
            print("4. Quit")
            choice = ask_int(">", 1, 4)
            if choice == 3:
                self.help_screen()
                continue
            break

        if choice == 1:
            self.new_game()
        elif choice == 2:
            if not self.load_game():
                print("Couldn't load a save. Starting a new game instead.")
                self.new_game()
        else:
            print("Thanks for visiting Eldoria.")
            return
        self.main_loop()

    def new_game(self) -> None:
        title("Create your Hero")
        name = ask("Hero name: ") or "Traveler"
        print("\nChoose your class:")
        print("1. Warrior - extra health and strong melee attacks")
        print("2. Mage - extra energy and powerful spells")
        print("3. Ranger - balanced stats and better gathering")
        choice = ask_int(">", 1, 3)
        classes = {1: "Warrior", 2: "Mage", 3: "Ranger"}
        hero_class = classes[choice]
        self.player = Player(name, hero_class)
        self.start_time = time.time()

        if hero_class == "Warrior":
            self.player.max_hp += 25
            self.player.hp = self.player.max_hp
            self.player.base_attack += 2
            self.player.inventory["Iron Sword"] = 1
            self.player.weapon = "Iron Sword"
        elif hero_class == "Mage":
            self.player.max_energy += 25
            self.player.energy = self.player.max_energy
            self.player.base_attack += 1
            self.player.inventory["Apprentice Wand"] = 1
            self.player.weapon = "Apprentice Wand"
        else:
            self.player.base_defense += 1
            self.player.inventory["Hunter Bow"] = 1
            self.player.weapon = "Hunter Bow"
            self.player.inventory["Fishing Rod"] = 1

        self.give_initial_quests()
        title(f"Welcome, {name}")
        say("The village elder approaches you beneath the old oak. "
            "\"Strange lights have appeared in the hills. Help the people, "
            "learn what is happening, and be careful beyond the village.\"")
        self.player.journal.append("The village elder warns you about strange lights in the hills.")
        pause()

    def give_initial_quests(self) -> None:
        assert self.player is not None
        for key in ("herbs", "goblins", "wolves", "relic"):
            definition = next(q for q in QUEST_DEFINITIONS if q.key == key)
            self.player.quests[key] = Quest.from_dict(definition.to_dict())

    def help_screen(self) -> None:
        title("HOW TO PLAY")
        say("Use the numbered menus to choose actions. Travel between connected "
            "locations, explore dangerous areas, fight enemies, gather materials, "
            "complete quests, and improve your gear.")
        print("\nTips:")
        print("- Keep potions ready before entering dangerous areas")
        print("- Check your journal for quest objectives and hints")
        print("- Save often. Your save file is stored beside this Python file")
        print("- The Dragon's Lair is intended for a high level hero.")
        pause()

    def main_loop(self) -> None:
        if self.player is None:
            return
        while self.running:
            self.refresh_play_time()
            self.status_bar()
            print("\nWhat would you like to do?")
            options = [
                "Travel",
                "Explore this area",
                "Inventory and equipment",
                "Character and skills",
                "Quests",
                "Shop / inn / crafting",
                "Gather resources",
                "Journal and map",
                "Save game",
                "Quit game",
            ]
            for index, option in enumerate(options, 1):
                print(f"{index}. {option}")
            choice = ask_int(">", 1, len(options))
            actions = [
                self.travel, self.explore, self.inventory_menu,
                self.character_menu, self.quest_menu, self.town_menu,
                self.gather_menu, self.journal_menu, self.save_game,
                self.quit_to_title,
            ]
            actions[choice - 1]()
        print("Game closed")

    def explore(self) -> None:
        assert self.player is not None
        location = self.player.location
        subtitle(f"Exploring {location}")
            
        if WORLD[location]["danger"] > 0 and random.random() < 0.55:
            self.start_combat(location)
        elif random.random() < 0.65:
            item = self.find_resource(location)
            print(f"You found {item}.")
        else:
            print("You explore but find nothing.")
        pause()
        

    def character_menu(self) -> None:
        assert self.player is not None
        p = self.player
        subtitle("Character and Skills")
        print(f"Name: {p.name}")
        print(f"Class: {p.hero_class}")
        print(f"Level: {p.level} | XP: {p.xp}")
        print(f"Attack: {p.attack} | Defense: {p.defense}")
        print(f"Skill points: {p.skill_points}")
        print("Skills:")
        for skill, level in p.skills.items():
            print(f"- {skill}: {level}")
        pause()

    def quest_menu(self) -> None:
        assert self.player is not None
        p = self.player
        quests = list(p.quests.values())
        subtitle("Quests")

        if not quests:
            print("You have no active quests.")
            pause()
            return

        for index, quest in enumerate(quests, 1):
            if quest.complete and not quest.claimed:
                status = "Reward ready"
            elif quest.claimed:
                status = "Reward claimed"
            else:
                status = f"{quest.progress}/{quest.required}"
            print(f"{index}. {quest.name} - {status}")

        print("0. Back")
        choice = ask_int("Choose a quest or enter 0 to go back: ",
                         0, len(quests))

        if choice == 0:
            return

        quest = quests[choice - 1]

        if not quest.complete or quest.claimed:
            print("This quest has no reward ready to claim.")
        else:
            p.gold += quest.reward_gold
            p.gain_xp(quest.reward_xp)

            if quest.reward_item:
                p.add_item(quest.reward_item)

            quest.claimed = True
            print(f"Claimed reward for {quest.name}!")
            print(f"Received {quest.reward_gold} gold and "
                  f"{quest.reward_xp} XP.")

        pause()

    def town_menu(self) -> None:
        assert self.player is not None
        p = self.player
        features = WORLD[p.location].get("features", [])

        while True:
            subtitle("Shop / Inn / Crafting")
            print("1. Shop")
            print("2. Inn")
            print("3. Crafting")
            print("4. Back")

            choice = ask_int(">", 1, 4)

            if choice == 4:
                return

            elif choice == 1:
                if "shop" not in features:
                    print("There is no shop here.")
                else:
                    stock = [n for n in SHOP_STOCK if n in ITEMS]

                    for i, name in enumerate(stock, 1):
                        print(f"{i}. {name} - {ITEMS[name].value} gold")

                    print("0. Back")
                    selected = ask_int("Choose an item: ",
                                        0, len(stock))

                    if selected:
                        name = stock[selected - 1]
                        price = ITEMS[name].value

                        if p.gold < price:
                            print("Not enough gold.")
                        else:
                            p.gold -= price
                            p.add_item(name)
                            print(f"Bought {name}.")

                pause()

            elif choice == 2:
                if "inn" not in features:
                    print("There is no inn here.")
                elif p.gold < 10:
                    print("You need 10 gold to rest.")
                else:
                    p.gold -= 10
                    p.hp = p.max_hp
                    p.energy = p.max_energy
                    print("Your health and energy are restored.")

                pause()

            elif choice == 3:
                if "craft" not in features:
                    print("There is no crafting bench here.")
                else:
                    self.craft_menu()

    def quit_to_title(self) -> None:
        self.running = False
        print("Game ended.")

    def start_combat(self, location: str) -> None:
        assert self.player is not None
        p = self.player

        enemy_names = [
            name for name in AREA_ENEMIES.get(location, [])
            if name in ENEMIES
        ]

        if not enemy_names:
            print("No enemies were found here.")
            return

        enemy_name = random.choice(enemy_names)
        enemy = ENEMIES[enemy_name]
        enemy_hp = enemy.hp

        title(f"A {enemy_name} appears!")

        while enemy_hp > 0 and p.hp > 0:
            print(f"Your HP: {p.hp}/{p.max_hp}")
            print(f"{enemy_name} HP: {enemy_hp}/{enemy.hp}")
            print("1. Attack")
            print("2. Use consumable")
            print("3. Try to flee")

            choice = ask_int(">", 1, 3)

            if choice == 1:
                damage = max(
                    1, p.attack - enemy.defense + random.randint(-2, 2)
                )
                enemy_hp -= damage
                print(f"You deal {damage} damage.")

                if enemy_hp <= 0:
                    break

            elif choice == 2:
                self.use_consumable()

            else:
                if random.random() < 0.5:
                    print("You escaped safely.")
                    return
                print("You could not escape!")

            if enemy_hp > 0:
                damage = max(
                    1, enemy.attack - p.defense + random.randint(-1, 2)
                )
                p.hp -= damage
                print(f"{enemy_name} deals {damage} damage.")

        if p.hp <= 0:
            p.hp = max(1, p.max_hp // 2)
            p.location = "Oakheart Village"
            p.gold = max(0, p.gold - 10)
            print("You were defeated and returned to Oakheart Village.")
            return

        p.kills[enemy_name] = p.kills.get(enemy_name, 0) + 1
        p.gold += enemy.gold
        p.gain_xp(enemy.xp)
        p.update_quest_progress("kill", enemy_name, 1)

        print(f"You defeated {enemy_name}!")
        print(f"You gained {enemy.xp} XP and {enemy.gold} gold.")

        if enemy_name == "The Ashen Dragon":
            p.add_item("Dragon Heart")
            print("You received a Dragon Heart!")
    
    def refresh_play_time(self) -> None:
        if self.player:
            self.player.play_time = int(time.time() - self.start_time)

    def status_bar(self) -> None:
        assert self.player is not None
        p = self.player
        print()
        line()
        print(f"{p.name} the {p.hero_class} | Level {p.level} | Gold: {p.gold}")
        print(f"HP {p.hp}/{p.max_hp} {bar(p.hp, p.max_hp)}")
        print(f"EN {p.energy}/{p.max_energy} {bar(p.energy, p.max_energy)}")
        print(f"Location: {p.location}")
        line()

    def travel(self) -> None:
        assert self.player is not None
        location = WORLD[self.player.location]
        neighbours = location["neighbors"]
        subtitle(f"Travel from {self.player.location}")
        for index, name in enumerate(neighbours, 1):
            danger = WORLD[name]["danger"]
            print(f"{index}. {name} (danger {danger}/6)")
        print(f"{len(neighbours) + 1}. Stay here")
        choice = ask_int(">", 1, len(neighbours) + 1)
        if choice == len(neighbours) + 1:
            return
        destination = neighbours[choice - 1]
        self.player.location = destination
        self.player.steps += 1
        if destination not in self.player.visited:
            self.player.visited.append(destination)
            self.player.journal.append(f"Discovered {destination}.")
            print(f"You discovered {destination}!")
            self.player.gain_xp(10)
        say(WORLD[destination]["description"])
        self.random_travel_event(destination)
        self.player.check_achievements()

    def random_travel_event(self, destination: str) -> None:
        assert self.player is not None
        danger = WORLD[destination]["danger"]
        if danger <= 0:
            if random.random() < 0.15:
                found = random.randint(3, 12)
                self.player.gold += found
                print(f"You found {found} gold near the road.")
            return
        roll = random.random()
        if roll < min(0.18 + danger * 0.09, 0.65):
            self.start_combat(destination)
        elif roll < 0.78:
            event = random.choice(["herbs", "coins", "ambush_avoided", "nothing"])
            if event == "herbs":
                self.player.add_item("Herb", 1)
                self.player.update_quest_progress("gather", "Herb", 1)
                self.player.gathered["Herb"] = self.player.gathered.get("Herb", 0) + 1
                print("You spot a useful herb beside the path.")
            elif event == "coins":
                coins = random.randint(5, 18) + danger * 2
                self.player.gold += coins
                print(f"You find a pouch containing {coins} gold.")
            elif event == "ambush_avoided":
                print("You hear movement nearby and quietly avoid an ambush.")
            else:
                print("The road is quiet for now.")

    def find_resource(self, location: str) -> str:
        assert self.player is not None
        pools = {
            "forest": ["Herb", "Wolf Pelt"],
            "river": ["Herb"],
            "swamp": ["Herb", "Crystal Shard"],
            "cave": ["Iron Ore", "Crystal Shard", "Spider Silk"],
            "mountain": ["Iron Ore", "Crystal Shard"],
            "glade": ["Herb", "Crystal Shard"],
            "ruins": ["Iron Ore", "Ancient Relic"],
            "road": ["Herb", "Iron Ore"],
            "camp": ["Goblin Ear", "Wolf Pelt"],
            "hub": ["Herb", "Iron Ore"],
            "boss": ["Dragon Heart"],
        }
        area_type = WORLD[location]["type"]
        item = random.choice(pools.get(area_type, ["Herb"]))
        self.player.add_item(item, 1)
        self.player.gathered[item] = self.player.gathered.get(item, 0) + 1
        self.player.update_quest_progress("gather", item, 1)
        return item

    def inventory_menu(self) -> None:
        assert self.player is not None
        while True:
            subtitle("Inventory")
            if not self.player.inventory:
                print("Your bag is empty.")
            else:
                for idx, (name, count) in enumerate(sorted(self.player.inventory.items()), 1):
                    item = ITEMS.get(name, Item(name, "misc", ""))
                    print(f"{idx}. {name} x{count} - {item.description}")
            print("\n1. Use consumable\n2. Equip item\n3. Drop item\n4. Back")
            choice = ask_int(">", 1, 4)
            if choice == 1:
                self.use_consumable()
            elif choice == 2:
                self.equip_item()
            elif choice == 3:
                self.drop_item()
            else:
                return

    def use_consumable(self) -> bool:
        assert self.player is not None
        candidates = [
            n for n, c in self.player.inventory.items()
            if c > 0 and n in ITEMS and ITEMS[n].kind == "consumable"
        ]
        if not candidates:
            print("No consumables available.")
            return False
        for idx, name in enumerate(candidates, 1):
            print(f"{idx}. {name} x{self.player.inventory[name]}")
        print(f"{len(candidates) + 1}. Back")
        choice = ask_int(">", 1, len(candidates) + 1)
        if choice > len(candidates):
            return False
        name = candidates[choice - 1]
        self.player.remove_item(name)
        restored = self.player.heal(ITEMS[name].power)
        print(f"Restored {restored} HP.")
        return True

    def equip_item(self) -> None:
        assert self.player is not None
        candidates = [
            n for n, c in self.player.inventory.items()
            if c > 0 and n in ITEMS and ITEMS[n].kind in ("weapon", "armor", "accessory")
        ]
        if not candidates:
            print("Nothing to equip.")
            return
        for idx, name in enumerate(candidates, 1):
            print(f"{idx}. {name} ({ITEMS[name].kind})")
        print(f"{len(candidates) + 1}. Back")
        choice = ask_int(">", 1, len(candidates) + 1)
        if choice <= len(candidates):
            name = candidates[choice - 1]
            kind = ITEMS[name].kind
            if kind == "weapon":
                self.player.weapon = name
            elif kind == "armor":
                self.player.armor = name
            else:
                self.player.accessory = name
            print(f"Equipped {name}.")

    def drop_item(self) -> None:
        assert self.player is not None
        names = list(self.player.inventory)
        if not names:
            print("Nothing to drop.")
            return
        for idx, name in enumerate(names, 1):
            print(f"{idx}. {name}")
        print(f"{len(names) + 1}. Back")
        choice = ask_int(">", 1, len(names) + 1)
        if choice <= len(names):
            name = names[choice - 1]
            self.player.remove_item(name)
            print(f"Dropped {name}.")

    def craft_menu(self) -> None:
        assert self.player is not None
        while True:
            subtitle("Crafting Bench")
            for idx, (result, ingredients) in enumerate(CRAFTING_RECIPES.items(), 1):
                req = ", ".join(f"{cnt} {itm}" for itm, cnt in ingredients.items())
                print(f"{idx}. {result} <- {req}")
            print(f"{len(CRAFTING_RECIPES) + 1}. Back")
            choice = ask_int(">", 1, len(CRAFTING_RECIPES) + 1)
            if choice > len(CRAFTING_RECIPES):
                return
            result = list(CRAFTING_RECIPES)[choice - 1]
            ingredients = CRAFTING_RECIPES[result]
            if all(self.player.has_item(itm, cnt) for itm, cnt in ingredients.items()):
                for itm, cnt in ingredients.items():
                    self.player.remove_item(itm, cnt)
                self.player.add_item(result, 1)
                print(f"Crafted {result}.")
            else:
                print("Missing required materials.")

    def gather_menu(self) -> None:
        assert self.player is not None
        if random.random() < 0.75:
            item = self.find_resource(self.player.location)
            print(f"Gathered {item}.")
        else:
            print("Found nothing.")
        pause()

    def journal_menu(self) -> None:
        assert self.player is not None
        while True:
            subtitle("Journal")
            for entry in self.player.journal[-10:]:
                print(f"- {entry}")
            print("\n1. Back")
            if ask_int(">", 1, 1) == 1:
                return

    def save_game(self) -> None:
        assert self.player is not None
        payload = {"version": VERSION, "player": self.player.to_dict()}
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(payload, f, indent=2)
            print("Game saved.")
        except OSError as e:
            print(f"Save failed: {e}")
        pause()

    def load_game(self) -> bool:
        if not os.path.exists(SAVE_FILE):
            return False
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                payload = json.load(f)
            self.player = Player.from_dict(payload["player"])
        except (OSError, ValueError, KeyError, TypeError):
            return False
        # Keep play time continuing from the saved value instead of resetting it.
        self.start_time = time.time() - self.player.play_time
        return True


def main() -> None:
    random.seed()
    try:
        Game().start()
    except (KeyboardInterrupt, EOFError):
        print("\nGame interrupted")


if __name__ == "__main__":
    main()
