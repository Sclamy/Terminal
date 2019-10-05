import gamelib
import random
import math
import warnings
from sys import maxsize
import json


"""
Most of the algo code you write will be in this file unless you create new
modules yourself. Start by modifying the 'on_turn' function.

Advanced strategy tips: 

  - You can analyze action frames by modifying on_action_frame function

  - The GameState.map object can be manually manipulated to create hypothetical 
  board states. Though, we recommended making a copy of the map to preserve 
  the actual current map state.
"""


def cprint(message):
    gamelib.debug_write(message)
    return


def path_to_enemy_edge(game_state, path):
    hostile_edges = (game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT) +
                     game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT))
    if path is not None and path[-1] in hostile_edges:
        pathToEdge = True
    else:
        pathToEdge = False

    return pathToEdge


def find_least_dmg_to_edge(game_state, dmg_thresh):
    friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                      game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))

    # game_state_sim = game_state

    bestPath = [1000, []]  # 1000 (max) damage, empty path
    for location in friendly_edges:
        path = game_state.find_path_to_edge(location)
        if path_to_enemy_edge(game_state, path):
            foundPath = True
            damage = 0
            for path_location in path:
                # Get number of enemy destructors that can attack the final location and multiply by destructor damage
                damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR,
                                                                                             game_state.config).damage
            if damage < bestPath[0] and damage <= dmg_thresh:
                bestPath[0] = damage
                bestPath[1] = path

    if bestPath[0] < 1000:
        cprint(f'Clear, ideal path to enemy edge with {damage} damage')
        cprint(f'{bestPath[1]}')
    else:
        cprint('No path to enemy edge')

    return bestPath[1]


def paths_to_score(game_state):

    return


def least_damage_spawn_location(game_state):
    """
    This function will help us guess which location is the safest to spawn moving units from.
    It gets the path the unit will take then checks locations on that path to
    estimate the path's damage risk.
    """
    damages = []

    friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                      game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))
    hostile_edges = (game_state.game_map.get_edge_locations(game_state.game_map.TOP_LEFT) +
                     game_state.game_map.get_edge_locations(game_state.game_map.TOP_RIGHT))
    # friendly_edges = [[x, y+1] for x, y in friendly_edges]

    # Get the damage estimate each path will take
    for location in friendly_edges:
        path = game_state.find_path_to_edge(location)
        damage = 0
        if path is None or path[-1] not in hostile_edges:  # this needs verification...
            damages.append(1000)
            continue
        else:
            cprint(f"This is a legit path, starting at {path[0]} and ending at {path[-1]}.")
        for path_location in path:
            # Get number of enemy destructors that can attack the final location and multiply by destructor damage
            damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage
        damages.append(damage)

    # Now just return the location that takes the least damage
    if min(damages) < 1000:
        return friendly_edges[damages.index(min(damages))], min(damages)
    else:
        return None, 1000


def most_damage_spawn_location(game_state):
    """
    This function will help us guess which location is the safest to spawn moving units from.
    It gets the path the unit will take then checks locations on that path to
    estimate the path's damage risk.
    """
    damages = []

    friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                      game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))
    # friendly_edges = [[x, y+1] for x, y in friendly_edges]

    # Get the damage estimate each path will take
    for location in friendly_edges:
        path = game_state.find_path_to_edge(location)
        damage = 0
        if path is None:
            damages.append(0)
            continue
        for path_location in path:
            # Get number of enemy destructors that can attack the final location and multiply by destructor damage
            damage += len(game_state.get_attackers(path_location, 0)) * gamelib.GameUnit(DESTRUCTOR, game_state.config).damage
        damages.append(damage)

    # Now just return the location that takes the least damage
    if max(damages) > 0:
        return friendly_edges[damages.index(max(damages))], max(damages)
    else:
        return None, 0


def build_defences(game_state):
    """
    Build basic defenses using hardcoded locations.
    Remember to defend corners and avoid placing units in the front where enemy EMPs can attack them.
    """
    # Useful tool for setting up your base locations: https://www.kevinbai.design/terminal-map-maker
    # More community tools available at: https://terminal.c1games.com/rules#Download

    first_filter_locations = [[0, 13], [27, 13], [1, 13], [26, 13], [2, 13], [25, 13], [3, 12], [24, 12],
                              [4, 11], [23, 11], [5, 10], [22, 10], [6, 11], [21, 11], [7, 10], [20, 10],
                              [8, 9], [19, 9], [9, 8], [18, 8], [10, 7], [17, 7], [11, 6], [16, 6], [12, 6], [15, 6]
                              ]
    game_state.attempt_spawn(FILTER, first_filter_locations)
    for filter_location in first_filter_locations:
        thing = game_state.game_map[filter_location[0], filter_location[1]][0]
        if thing and thing.unit_type == 'FILTER'and thing.stability <= 20:
            game_state.attempt_remove(filter_location)
    # Place destructors that attack enemy units
    destructor_locations_0 = [[12, 5], [15, 5], [6, 10], [21, 10], [2, 12], [25, 12], [12, 4], [15, 4]]
    for location in destructor_locations_0:
        game_state.attempt_spawn(DESTRUCTOR, [location])
        # game_state.attempt_spawn(FILTER, [[location[0], location[1] + 1]])

    if game_state.get_resource(game_state.CORES) < 6:
        return

    if game_state.turn_number > 4:
        encryptor_locations_0 = [[13, 2], [14, 2]]
        game_state.attempt_spawn(ENCRYPTOR, encryptor_locations_0)

    # Place filters to guide paths
    # filter_locations = [[0, 13], [1, 13], [2, 13], [25, 13], [26, 13], [27, 13], [3, 12], [4, 12], [23, 12],
    #                    [24, 12], [4, 11], [5, 11], [13, 11], [14, 11], [22, 11], [23, 11], [5, 10], [6, 10],
    #                    [8, 10], [9, 10], [12, 10], [15, 10], [18, 10], [19, 10], [21, 10], [22, 10], [9, 9],
    #                    [10, 9], [17, 9], [18, 9]]
    # game_state.attempt_spawn(FILTER, filter_locations)
    encryptor_locations = [[11, 3], [16, 3]]
    game_state.attempt_spawn(ENCRYPTOR, encryptor_locations)

    destructor_locations_2 = [[2, 11], [25, 11], [4, 9], [13, 9], [14, 9], [23, 9], [8, 8], [19, 8]]
    game_state.attempt_spawn(DESTRUCTOR, destructor_locations_2)


class AlgoStrategy(gamelib.AlgoCore):
    def __init__(self):
        super().__init__()
        seed = random.randrange(maxsize)
        random.seed(seed)
        gamelib.debug_write('Random seed: {}'.format(seed))

    def on_game_start(self, config):
        """ 
        Read in config and perform any initial setup here 
        """
        gamelib.debug_write('Configuring your custom algo strategy...')
        self.config = config
        global FILTER, ENCRYPTOR, DESTRUCTOR, PING, EMP, SCRAMBLER
        FILTER = config["unitInformation"][0]["shorthand"]
        ENCRYPTOR = config["unitInformation"][1]["shorthand"]
        DESTRUCTOR = config["unitInformation"][2]["shorthand"]
        PING = config["unitInformation"][3]["shorthand"]
        EMP = config["unitInformation"][4]["shorthand"]
        SCRAMBLER = config["unitInformation"][5]["shorthand"]
        # This is a good place to do initial setup
        self.scored_on_locations = []


    def on_turn(self, turn_state):
        """
        This function is called every turn with the game state wrapper as
        an argument. The wrapper stores the state of the arena and has methods
        for querying its state, allocating your current resources as planned
        unit deployments, and transmitting your intended deployments to the
        game engine.
        """
        game_state = gamelib.GameState(self.config, turn_state)
        gamelib.debug_write('Performing turn {} of your custom algo strategy'.format(game_state.turn_number))
        game_state.suppress_warnings(True)  # Comment or remove this line to enable warnings.

        # self.starter_strategy(game_state)
        self.khan(game_state)

        game_state.submit_turn()

    """
    NOTE: All the methods after this point are part of the sample starter-algo
    strategy and can safely be replaced for your custom algo.
    """

    def khan(self, game_state):
        # Start with 40 Cores, 5 Bits

        # Offensive Defences  - Total cost, 40
        pink_destructors_points = [[8, 7], [19, 7]]
        pink_filters_points = [[0, 13], [1, 13], [2, 13], [3, 13], [24, 13], [25, 13], [26, 13], [27, 13], [3, 12],
                               [4, 12], [23, 12], [24, 12], [4, 11], [5, 11], [22, 11], [23, 11], [6, 10], [21, 10],
                               [6, 9], [7, 9], [20, 9], [21, 9], [7, 8], [8, 8], [19, 8], [20, 8], [9, 7], [18, 7]]
        game_state.attempt_spawn(DESTRUCTOR, pink_destructors_points)
        game_state.attempt_spawn(FILTER, pink_filters_points)
        # game_state.attempt_spawn(ENCRYPTOR, pink_encryptors_points)

        # Guidence Defences
        # teal_filters_points = [[10, 10], [17, 10], [9, 9], [18, 9], [8, 8], [19, 8], [7, 7], [20, 7]]
        # game_state.attempt_spawn(FILTER, teal_filters_points)

        # Expansion Defences
        blue_destructors_points = [[13, 6], [14, 6]]
        blue_filters_points = [[13, 7], [14, 7], [12, 6], [15, 6]]
        blue_encryptors_points = [[13, 4], [14, 4], [13, 5], [14, 5]]
        game_state.attempt_spawn(DESTRUCTOR, blue_destructors_points)
        game_state.attempt_spawn(FILTER, blue_filters_points)
        game_state.attempt_spawn(ENCRYPTOR, blue_encryptors_points)

        red_destructors_points = [[2, 12], [25, 12], [5, 10], [22, 10], [3, 11], [24, 11]]
        game_state.attempt_spawn(DESTRUCTOR, red_destructors_points)

        # Spawning
        least_damage_spawn, least_damage = least_damage_spawn_location(game_state)
        cprint(f"Least damage: {least_damage}")
        if least_damage < 2:  # Gottem Case
            game_state.attempt_spawn(PING, least_damage_spawn, 1000)

        most_damage_spawn, most_damage = most_damage_spawn_location(game_state)
        cprint(f"Most damage: {most_damage}")
        # if most_damage > 1:  # can actually do damage
        #    if game_state.get_resource(game_state.BITS) > 14:  # 2.3
        #        game_state.attempt_spawn(EMP, most_damage_spawn, 1000)
        if game_state.get_resource(game_state.BITS) > 14:  # 2.3
            game_state.attempt_spawn(EMP, least_damage_spawn, 1000)


    def starter_strategy(self, game_state):
        """
        For defense we will use a spread out layout and some Scramblers early on.
        We will place destructors near locations the opponent managed to score on.
        For offense we will use long range EMPs if they place stationary units near the enemy's front.
        If there are no stationary units to attack in the front, we will send Pings to try and score quickly.
        """
        # First, place basic defenses
        build_defences(game_state)
        # Now build reactive defenses based on where the enemy scored
        # self.build_reactive_defense(game_state)

        if game_state.turn_number < 3:  # First 3 turns
            self.stall_with_scramblers(game_state, 1)
            self.stall_with_scramblers(game_state, 1)

        if game_state.get_resource(game_state.BITS, 1) > 20:  # Enemy has >20 resources (probably going to attack soon)
            self.stall_with_scramblers(game_state, 3)
            self.stall_with_scramblers(game_state, 3)

        # if game_state.get_resource(game_state.BITS) > (5 + (game_state.turn_number / 10)) * 2.1:  # 2.3
        if game_state.get_resource(game_state.BITS) > 14:  # 2.3
            best_location = None
            best_path_ping = find_least_dmg_to_edge(game_state, 5)
            if best_path_ping:
                attackUnit = PING
                best_location = best_path_ping[0]

            else:
                best_path_emp = find_least_dmg_to_edge(game_state, 100)
                if best_path_emp:
                    attackUnit = EMP
                    best_location = best_path_emp[0]

            if best_location:
                game_state.attempt_spawn(attackUnit, best_location, 1000)

        if game_state.get_resource(game_state.BITS) > 20:  # 2.3
            game_state.attempt_spawn(EMP, [13, 0], 1000)
        # find_breakthru(game_state)
        # paths_to_score(game_state)


    def build_reactive_defense(self, game_state):
        """
        This function builds reactive defenses based on where the enemy scored on us from.
        We can track where the opponent scored by looking at events in action frames 
        as shown in the on_action_frame function
        """
        for location in self.scored_on_locations:
            # Build destructor one space above so that it doesn't block our own edge spawn locations
            build_location = [location[0], location[1]+1]
            game_state.attempt_spawn(DESTRUCTOR, build_location)

    def stall_with_scramblers(self, game_state, numScramblers):
        """
        Send out Scramblers at random locations to defend our base from enemy moving units.
        """
        # We can spawn moving units on our edges so a list of all our edge locations
        friendly_edges = (game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_LEFT) +
                          game_state.game_map.get_edge_locations(game_state.game_map.BOTTOM_RIGHT))
        
        # Remove locations that are blocked by our own firewalls 
        # since we can't deploy units there.
        deploy_locations = self.filter_blocked_locations(friendly_edges, game_state)
        
        # While we have remaining bits to spend lets send out scramblers randomly.
        deploy_index = random.randint(0, len(deploy_locations) - 1)
        deploy_location = deploy_locations[deploy_index]

        game_state.attempt_spawn(SCRAMBLER, deploy_location, numScramblers)
        """
        We don't have to remove the location since multiple information 
        units can occupy the same space.
        """

    def emp_line_strategy(self, game_state):
        """
        Build a line of the cheapest stationary unit so our EMP's can attack from long range.
        """
        # First let's figure out the cheapest unit
        # We could just check the game rules, but this demonstrates how to use the GameUnit class
        stationary_units = [FILTER, DESTRUCTOR, ENCRYPTOR]
        cheapest_unit = FILTER
        for unit in stationary_units:
            unit_class = gamelib.GameUnit(unit, game_state.config)
            if unit_class.cost < gamelib.GameUnit(cheapest_unit, game_state.config).cost:
                cheapest_unit = unit

        # Now let's build out a line of stationary units. This will prevent our EMPs from running into the enemy base.
        # Instead they will stay at the perfect distance to attack the front two rows of the enemy base.
        for x in range(27, 5, -1):
            game_state.attempt_spawn(cheapest_unit, [x, 11])

        # Now spawn EMPs next to the line
        # By asking attempt_spawn to spawn 1000 units, it will essentially spawn as many as we have resources for
        game_state.attempt_spawn(EMP, [24, 10], 1000)

    def detect_enemy_unit(self, game_state, unit_type=None, valid_x = None, valid_y = None):
        total_units = 0
        for location in game_state.game_map:
            if game_state.contains_stationary_unit(location):
                for unit in game_state.game_map[location]:
                    if unit.player_index == 1 and (unit_type is None or unit.unit_type == unit_type) and (valid_x is None or location[0] in valid_x) and (valid_y is None or location[1] in valid_y):
                        total_units += 1
        return total_units
        
    def filter_blocked_locations(self, locations, game_state):
        filtered = []
        for location in locations:
            if not game_state.contains_stationary_unit(location):
                filtered.append(location)
        return filtered

    def on_action_frame(self, turn_string):
        """
        This is the action frame of the game. This function could be called 
        hundreds of times per turn and could slow the algo down so avoid putting slow code here.
        Processing the action frames is complicated so we only suggest it if you have time and experience.
        Full doc on format of a game frame at: https://docs.c1games.com/json-docs.html
        """
        # Let's record at what position we get scored on
        state = json.loads(turn_string)
        events = state["events"]
        breaches = events["breach"]
        for breach in breaches:
            location = breach[0]
            unit_owner_self = True if breach[4] == 1 else False
            # When parsing the frame data directly, 
            # 1 is integer for yourself, 2 is opponent (StarterKit code uses 0, 1 as player_index instead)
            if not unit_owner_self:
                # gamelib.debug_write("Got scored on at: {}".format(location))
                self.scored_on_locations.append(location)
                # gamelib.debug_write("All locations: {}".format(self.scored_on_locations))


if __name__ == "__main__":
    algo = AlgoStrategy()
    algo.start()
