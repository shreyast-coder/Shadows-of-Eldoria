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
