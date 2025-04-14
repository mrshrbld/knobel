import numpy as np

## Define classes
## Player class
class player:
    def __init__(self, name='player0', input='-', points=0, sum=0):
        self.name = name
        self.input = input
        self.points = points
        self.sum = sum
    
    def check(self, input):
        """
        Check if input of player is valid
        """
        dice2points = { '0':0,  '104':5,  '105':10, '106':15, '107':20, '108':25,
                        '109':30, '110':35, '122':40, '123':45, '124':50,
                        '125':55, '162':60, '163':65, '164':70, '165':75,
                        '202':80, '203':85, '204':90, '205':95,  '220':100,
                        '260':105, 'g111':110, '222':120, '333':130, '444':140,
                        '555':150, '666':160, '111':180, '234':115, '345':125,
                        '456':190, '1,2,3':200
                      }
        try:
            points = dice2points[input]
        except:
            points = 'not valid'
        return points

## Define the 'game' class
class game:
# Initialization of class object
    def __init__(self, players_list=['player0'], rounds_tables=4,
                 players_table=4):
        """
        Input vars:
        'players' is an array of the players
        'rounds_tables' is an integer of the total rounds of played tables
        'players_table' is an integer of the maximum players at a table

        Init vars:
        'self.players' is the array of players
        'self.rounds_tables' is an integer of the maximum rounds of tables
        'self.no_players' is an integer of the total number of players
        'self.players_table' is an integer of the maximum players at a table
        'unsual_tables' is a list of tables with the maximum players -1
        'usual_tables' is a list of tables with the maximum players
        'self.layout_tables' is an array with the usual and unusual tables
        """
    # Create players
        players = []
        # Load players list
        if players_list == []:
            players_list = np.loadtxt('list_players.txt', dtype=str)
        for entry in players_list:
            players.append(player(name=entry))
        # print([player.name for player in players])
        print(type(players))
        self.players = np.array(players)
        # print([player.name for player in self.players])
        print(type(self.players))
        
    # Initialization of settings
        self.rounds_tables = rounds_tables # max rounds
        self.round_tables = 0 # current round
        self.no_players = len(self.players)
        self.players_table = players_table

    # An array defining the layout of the tables
        unsual_tables = ([self.players_table-1]*
                         (self.players_table-(self.no_players % self.players_table)
                         if (self.no_players % self.players_table)!=0 else 0))
        usual_tables = ([self.players_table]*((self.no_players-sum(unsual_tables))
                                               // self.players_table))

        self.layout_tables = np.array(usual_tables + unsual_tables)

    # Pepare an two-dimensional array (dim1 players, dim2 round_tables)
    # defining a random order of the players and in the same time the
    # players per table per round.
        self.tables_players = np.repeat(np.expand_dims(self.players, axis=1),
                                         self.rounds_tables, axis=1)
        for i in range(self.rounds_tables):
            self.tables_players[:,i] = np.random.default_rng().permutation(
                                        self.tables_players[:,0]
                                                                          )
    
    def create_round(self):
        """"
        """
        # maybe control if-statemnt useful to prevent overwriting of current round
        tables = []
        # print("self.layout_tables: {}".format(self.layout_tables))
        # Check this for 5 players problem occurs
        for i in range(len(self.layout_tables)):
            players = np.take(self.tables_players[:,0],range(np.sum(self.layout_tables[:i]),
                                                        np.sum(self.layout_tables[:i+1])))
            t = table(index=i, players=players)
            tables.append(t)
        self.tables = np.array(tables)
        # Create string for url restrictions
        self.str_valid_tables_index = "'"+"', '".join(str(s) for s in 
                                 [getattr(table, 'index') for table in g.tables])+"'"

k=game(players_list=[])
# print(k, vars(k))
print('k.layout_tables: {} '.format(k.layout_tables))
print('k.players: {}'.format(type(k.players)))
# print([player.name for player in k.players])
print(type(k.players))