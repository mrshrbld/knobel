### Set environment
## General Stuff
# Lines are written up to column 75-80
# print() statements only for development and will be deleted later
master_key = 2410
existing_game = False
settings_fixed = 'False'
end_game = False

## Load needed modules
import numpy as np
import logging
from flask import Flask, render_template, request, redirect, abort
from uuid import uuid4
from datetime import datetime
from random import randint

## Set logger options
logger = logging.getLogger(__name__)
#logging.basicConfig(filename='log.txt', level=logging.DEBUG, filemode='w')

### Define classes
## Player class
class player:
    def __init__(self, name='player0', input='-', points=0, sum=0):
        self.name = name
        self.input = input
        self.points = points
        self.sum = sum
        self.sum_history = []
    
    def check(self, input):
        """
        Check if input of player is valid
        """
        dice2points = { '0':0,  '104':5,  '105':10, '106':15, '107':20, '108':25,
                        '109':30, '110':35, '122':40, '123':45, '124':50,
                        '125':55, '162':60, '163':65, '164':70, '165':75,
                        '202':80, '203':85, '204':90, '205':95,  '220':100,
                        '260':105, 'g111':110, '222':120, '333':130, '444':140,
                        '555':150, '666':160, '111':180, '2,3,4':165, '3,4,5':175,
                        '4,5,6':190, '1,2,3':200
                      }
        try:
            points = dice2points[input]
        except:
            points = 'not valid'
        return points

    def save_history(self):
        """
        Save sum to players history
        Reset inputs, points, sum
        """
        self.sum_history.append(self.sum)
        self.input = '-'
        self.points = 0
        self.sum = 0
        # print('player: {} Sum2history: {} history: {}'.format(self.name, self.sum, self.sum_history))


## Define the 'game' class
class game:
# Initialization of class object
    def __init__(self, players_list=['player0'], rounds_tables=4,
                 players_table=4, rounds_table=25):
        """
        Input vars:
        'players' is an array of the players
        'rounds_tables' is an integer of the total rounds of played tables
        'players_table' is an integer of the maximum players at a table
        'rounds_table' is an integer of the total rounds at a table

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
        self.players = np.array(players)
        
    # Initialization of settings
        self.rounds_tables = rounds_tables # max rounds
        self.round_tables = 0 # current round
        self.no_players = len(self.players)
        self.players_table = players_table
        self.rounds_table = rounds_table # max rounds at a table
    
    # An array defining the layout of the tables
        unsual_tables = ([self.players_table-1]*
                         (self.players_table-(self.no_players % self.players_table)
                         if (self.no_players % self.players_table)!=0 else 0))
        usual_tables = ([self.players_table]*((self.no_players-sum(unsual_tables))
                                               // self.players_table))

        self.layout_tables = np.array(usual_tables + unsual_tables)
        print()

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
        """
        """
        # maybe control if-statemnt useful to prevent overwriting of current round
        tables = []
        print("self.layout_tables: {}".format(self.layout_tables))
        # Check this for 5 players, problem occurs
        # layout_tables contains usual_tables (players_table as specified)
        # and unusual tables (players_table - 1)
        # no_players = 5 leads to 3 tables with 3 players -> that not possible
        # BUT effort is too large to fix it NOW and problem is not that important
        for i in range(len(self.layout_tables)):
            players = np.take(self.tables_players[:,self.round_tables],range(np.sum(self.layout_tables[:i]),
                                                        np.sum(self.layout_tables[:i+1])))
            t = table(index=i, players=players, rounds_table=self.rounds_table)
            tables.append(t)
        self.tables = np.array(tables)
    
    def closing(self):
        """
        Function to analyze some closing data to show at game_end.html screen
        """
        table = []
        # Add here more detailed analysis about table and the players
        # How many times points in certain ranges (how often 1,2,3 etc.)
        for player in self.players:
            player.sum_history = np.array(player.sum_history)
            player.sum = player.sum_history.sum()
            table_entry = []
            table_entry.append(player.name)
            table_entry.append(player.sum)
            for value in player.sum_history:
                table_entry.append(value)
            table.append(table_entry)
            print(vars(player))
        print(table)
        table = np.array(table)
        table = np.flip(table[np.argsort(table[:,1])], axis=0)
        return table

## Table class        
class table:
    def __init__(self, index=0, players=np.array([player()]), rounds_table=25):
        self.index = index
        self.players = players
        self.rounds_table = rounds_table # max rounds_table
        self.round = 0 # Current round
        self.create()
        self.active = False
        self.ending = False
        self.finished = False
        self.pin = randint(1000,9999)
        # # only for testing
        # if self.index in [0,1,2]:
        #     self.save(np.loadtxt('tableX_data.txt', dtype=str, skiprows=2))
        #     self.back2round()
        # # only for testing

    def check(self):
        """
        Check if input of players are valid
        """
        for player in self.players:
            if player.points == 'not valid':
                return False
        for player in self.players:
            player.sum += player.points
        return True

    def create(self):
        """
        Create file for data
        """
        data = np.reshape(np.concatenate((np.array(['']),
                               np.array([['', player.name, ''] for player in self.players]).flatten(),
                               np.array(['Round']),
                               np.array([['input', 'points', 'sum'] for player in self.players]).flatten()),axis=0),(2,-1))
        format = ['%8s'] + ['%8s', '%8s', '%8s']*len(self.players)
        np.savetxt('table{}_data.txt'.format(self.index),
                    data, fmt=format
                  )

    def save(self, data=np.array([[]])):
        """
        Fill infos!
        """
        if data.shape==np.array([[]]).shape:
            data = np.reshape(np.concatenate((np.array([self.round]),
                    np.array([[player.input, player.points, player.sum] \
                              for player in self.players]).flatten()),
                              axis=0),(1,-1)
                              )
        format = ['%8s'] + ['%8s', '%8s', '%8s']*len(self.players)
        with open('table{}_data.txt'.format(self.index), 'a') as file:
            np.savetxt(file, data, fmt=format)
        self.round += 1
        self.time_last_save = datetime.now()

    def update(self, round):
        """
        Correct line of round in file and update the whole file.
        """
        # Load table_data file
        file = np.loadtxt('table{}_data.txt'.format(self.index), skiprows=2, dtype=str)
        # Expand array-dims if needed
        if file.ndim == 1:
            file = np.expand_dims(file, axis=0)
        # Find line/round to update in file
        no_line = np.argwhere(np.array(file[:,0], dtype=int)==round)[0,0]
        for no_player in range(len(self.players)):
            file[no_line, no_player*3+1] = self.players[no_player].input
            delta_points = self.players[no_player].points - int(file[no_line, no_player*3+2])
            file[no_line, no_player*3+2] = self.players[no_player].points
            if delta_points!=0:
                for no_data in range(no_line, len(file)):
                    file[no_data, no_player*3+3] = int(file[no_data, no_player*3+3]) \
                                                   + delta_points
        file = np.array(file, dtype=str)
        self.create()
        self.save(data=file)
        self.back2round() 

        # with open('table{}_data.txt'.format(self.index), 'a') as file:
        #     for line in file:
        #         file.write(line)
        #         if line.split()[0] == round:
        #             print(line)
        #             break
        # # return
    
    def back2round(self, round=-1):
        """
        Function to set table back to certain round
        """
        data_return = np.loadtxt('table{}_data.txt'.format(self.index), skiprows=2, dtype=str)
        if data_return.ndim == 1:
            data_return = np.expand_dims(data_return, axis=0)
        if round == -1:
            round = data_return[-1,0]
            data_return = data_return[data_return[:,0]==str(round)]
            self.round = int(round) + 1
        else:
            data_return = data_return[data_return[:,0]==str(round)]
            self.round = int(data_return[0,0])
        # print('data_return {} table.round {}'.format(data_return, self.round))
        for no in range(len(self.players)):
            self.players[no].input = data_return[0,no*3+1]
            self.players[no].points = int(data_return[0,no*3+2])
            self.players[no].sum = int(data_return[0,no*3+3])
    
    def auth_token(self):
        """
        Create unique authentification token for table
        """
        token = uuid4()
        return token
    
    def closing(self):
        """
        Function to analyze some closing data to show at table_end.html screen
        """
        table = []
        # Add here more detailed analysis about table and the players
        # How many times points in certain ranges (how often 1,2,3 etc.)
        for player in self.players:
            if self.round-1 == self.rounds_table:
                table.append([player.name, player.sum, player.sum/self.rounds_table])
            else:
                table.append([player.name, player.sum, player.sum/self.round])
        table = np.array(table)
        table = np.flip(table[np.argsort(table[:,1])], axis=0)
        return table
    
### Main functionality

### Flask specific stuff
app = Flask(__name__)

## Flask functions Game
# Start gane
def game_start():
    """
    Option for table settings needed here!
    """
    global existing_game
    global settings_fixed
    #initialize game if it does not exist
    if not(existing_game):
        existing_game = True # needs to be adapted as table input options
        # These following 'standard' parameters are somehow redundant
        # in the class definition
        players_list = ['player0']
        rounds_tables = 5
        players_table = 4
        rounds_table = 25
        no_players = 1
    elif settings_fixed == 'False':
        players_list = request.form['players_list']
        rounds_tables = int(request.form['rounds_tables'])
        players_table = int(request.form['players_table'])
        rounds_table = int(request.form['rounds_table'])
        settings_fixed = request.form['settings_fixed']
        # Quick'n'dirty for number of players
        no_players = players_list.count(',')+1
        # # For testing only
        # settings_fixed = 'True'
        # # For testing only
        if settings_fixed == 'True':
            players_list = players_list.split(',')
            global g
            g = game(players_list=players_list, rounds_tables=rounds_tables,
                    players_table=players_table, rounds_table=rounds_table)
            # print('players_list: {}'.format(players_list))
            # print('g.layout_tables: {}'.format(g.layout_tables))
            # print('g.players: {}'.format(type(g.players)))
            g.create_round()
            return redirect(f"/round")
    elif settings_fixed and existing_game:
        return redirect(f"/round")
    return render_template('game.html', rounds_tables=rounds_tables,
                                players_table=players_table,
                                players_list=players_list,
                                rounds_table=rounds_table,
                                no_players=no_players,
                                settings_fixed=settings_fixed)

def game_restart():
    """
    Restart the game
    """
    # Currently not necessary!!!
    global existing_game
    global settings_fixed
    existing_game = False
    settings_fixed = 'False'
    return redirect(f"/game")

def game_load():
    """
    Option 2 load a game at a certain status/round
    """
    return 'game_load() Feature to include later'

def game_points():
    """
    Show live game points of all players
    """
    list = []
    for player in g.players:
            list.append([player.name, int(np.array(player.sum_history).sum()+player.sum)])
    list = np.array(list)
    list = np.flip(list[np.argsort(list[:,1])], axis=0)
    return render_template('table_end.html', data=list,
                                range_players=range(len(g.players)))

def game_end():
    """
    End game and show closing ceremony
    """
    global end_game
        # end screen of game (leaderboard, later build option for ceremony act)
        # option for later: players can be included for rest of the game
        # option for later: live update of the points per player
    if not(end_game):
        return redirect(f"/game")
    else:
        for player in g.players:
            player.save_history()
        g.round_tables += 1
        return render_template('table_end.html', data=g.closing(),
                                range_players=range(len(g.players)))
        # for better traceability change table_end to end_screen or something

def round_tables():
    """
    """
    try:
        # print('g.round_tables: {}'.format(g.round_tables))
        for t in g.tables:
            end_round = False
            end_game = False
            # print('Table index: {} Round: {} Rounds-Table: {}'.format(table.index, table.round, table.rounds_table))
            # print('Condition: {}'.format(table.round >= table.rounds_table))
            if t.finished:
                pass
            else:
                break
            end_round = True
        if g.round_tables >= g.rounds_tables-1:
            end_game = True
        return render_template('round.html', game=g, range1=range(g.players_table), end_round=end_round, end_game=end_game)
        # return 'show table QR codes and overview of players at table'
            # play round at the different tables and update table data continuesly,
            # check if tables are at end
            # show overview of current game status (points, leaderboard, more options later)
    except:
        return redirect(f"/game")

def round_tables_end():
    """
    End round_tables
    """
    # print('current round {}'.format(g.round_tables))
    for player in g.players:
        player.save_history()
    g.round_tables += 1
    g.create_round()
    return redirect(f"/round")

def round_tables_save():
    """
    Save round_tables
    """
        # develope file format for save game
        # -> array with including players and points,
        # general settings(rounds_tables, round_tables), tables_players,
        # offers the option for a loading function
        # after round save data of the round in game object
        # start the next round

## Flask functions Table
# Open a table
def table_start(index):
    """
    Root of the valid tables
    Overview of the table
        Input possibility -> not necessary anymore
        Table of last inputs
        Options to Check(and Save) and Correct last input
        Some simple analysis (leading players, average, ...) -> future feature
        Short status message -> not necessary anymore
    """
    try:
        index = int(index)
        global g
        table_check_index(index)
        # Check if table is finished and go to table_end
        if g.tables[index].finished:
            return redirect(f"/table{index}/end")
        # Load table data from file for overview
        # Also option to start a table at certain status 
        # by manipulating the specific file
        data = np.loadtxt('table{}_data.txt'.format(index), skiprows=2, dtype=str)
        if data.ndim == 1:
            data = np.expand_dims(data, axis=0)
        data = np.flip(data, axis=0)[:5]
        # Check table for end/exit condition
        if g.tables[index].round >= g.tables[index].rounds_table:
            g.tables[index].ending = True
        # Continue table normally
        # Check if toke is already defined (input only from one tab)
        if not(g.tables[index].active):
            # First tab of table to input data
            g.tables[index].active = True
            return render_template('table.html', table=g.tables[index], data=data, 
                            range_players=range(len(g.tables[index].players)))
        else:
            # Render only overview of table, to restrict input only from one tab
            return render_template('table_view.html', table=g.tables[index], data=data, 
                            range_players=range(len(g.tables[index].players)))
    except:
        return redirect(f"/game")

# Check index
def table_check_index(index):
    """
    Check if index exists in game
    """
    index = int(index)
    global g
    # print('index: {} type: {} len g.tables: {} type: {}'. \
    #       format(index, type(index), len(g.tables), type(len(g.tables))))
    # print('True/False: {}'.format(not(index < len(g.tables))))
    if not(index < len(g.tables)):
        abort(404)


# Check the input of table
def table_read_check_input(index):
    """
    Check the inputs
    If check OK then immediatly go to save
    Else go back to input
    """
    # MAGIC HAPPENS after this line!!!
    index = int(index)
    global g
    table_check_index(index)
    pin = int(request.form['reload_pin'])
    # print('pin: {} type: {}'.format(pin, type(pin)))
    # print('g.tables.pin: {} type: {}'.format(g.tables[index].pin, type(g.tables[index].pin)))
    # print('Compare pin and g.tables.pin:', pin != g.tables[index].pin)
    if g.tables[index].pin != pin:
        return redirect(f"/table{index}")
    else:
        g.tables[index].active = False
    # Loop to request the inputs
    for player in g.tables[index].players:
        player.input = request.form[player.name]
        player.points = player.check(player.input)

    # Check if inputs are valid    
    if g.tables[index].check():
        # Check complete, ready to save
        # Maybe we can include table_save_input function here
        return redirect(f"/table{index}/save")
    else:
        # Check incomplete, correct input
        return redirect(f"/table{index}")

# Save the input of table
def table_save_input(index):
    """
    Save inputs to file
    """
    index = int(index)
    global g
    table_check_index(index)
    g.tables[index].save()
    return redirect(f"/table{index}")

# Correct the input of table
def table_correct_input(index):
    """
    Correct specific Input
    """
    index = int(index)
    global g
    table_check_index(index)
    round = int(request.form.get("round"))
    g.tables[index].back2round(round)
    return render_template('correct.html', table=g.tables[index])

# Update file and player stats of table after table_correct_input function
def table_update_stats(index):
    """
    Update the table[index]_data.txt file and the stats for the players
    """
    index = int(index)
    global g
    table_check_index(index)
    # Loop to request the corrected inputs
    players_update = g.tables[index].players
    # for player in players_update:
    for player in g.tables[index].players:
        player.input = request.form[player.name]
        player.points = player.check(player.input)
        # print('input {} points {}'.format(player.input, player.points))
    
    # Check if inputs are valid   
    if g.tables[index].check():
        # Check complete, ready to update
        g.tables[index].update(g.tables[index].round)
        g.tables[index].active = False
        return redirect(f"/table{index}")
    else:
        # Check incomplete, correct input
        return render_template('correct.html', table=g.tables[index])
    return 'update'

# Table reload from table_view
def table_reload(index):
    """"
    Reload table.html coming from table_view.html
    """
    index = int(index)
    global g
    table_check_index(index)
    pin = int(request.form['reload_pin'])
    # print('pin: {} type: {}'.format(pin, type(pin)))
    # print('g.tables.pin: {} type: {}'.format(g.tables[index].pin, type(g.tables[index].pin)))
    # print('Compare pin and g.tables.pin:', pin == g.tables[index].pin)
    if pin == g.tables[index].pin or pin == master_key:
        g.tables[index].pin = randint(1000,9999)
        g.tables[index].active = False
    return redirect(f"/table{index}")

def table_end(index):
    """
    """
    index = int(index)
    global g
    table_check_index(index)
    if not(g.tables[index].ending):
        return redirect(f"/table{index}")
    else:
        g.tables[index].finished = True
        return render_template('table_end.html', data=g.tables[index].closing(),
                                range_players=range(len(g.tables[index].players)))

## Flask call of servers game
# Initialize game
app.add_url_rule(f"/game",
                 view_func=game_start, methods=['GET', 'POST'])

# Restart game
app.add_url_rule(f"/game_restart",
                 view_func=game_restart, methods=['GET', 'POST'])

# Show game points for all players
app.add_url_rule(f"/game_points",
                 view_func=game_points, methods=['GET', 'POST'])

# End game
app.add_url_rule(f"/game_end",
                 view_func=game_end, methods=['GET', 'POST'])

# Start round of all tables
app.add_url_rule(f"/round",
                 view_func=round_tables, methods=['GET', 'POST'])

# Restart round of all tables
# Is it necessary?!

# End round of tables and start next round of tables if possible/necessary
app.add_url_rule(f"/round_end",
                 view_func=round_tables_end, methods=['GET', 'POST'])

## Flask call of servers table
# Open table
# similar to "@app.route("/table{}".format(i))" is "app.add_url_rule(...)"
app.add_url_rule(f"/table<int:index>",
                 view_func=table_start, methods=['GET', 'POST'])

# Read and check input of table
app.add_url_rule(f"/table<int:index>/check",
                 view_func=table_read_check_input, methods=['GET', 'POST'])

# Save input of table
app.add_url_rule(f"/table<int:index>/save",
                 view_func=table_save_input, methods=['GET', 'POST'])

# Correct input of table
app.add_url_rule(f"/table<int:index>/correct",
                 view_func=table_correct_input, methods=['GET','POST'])

# Update file of table
app.add_url_rule(f"/table<int:index>/update",
                 view_func=table_update_stats, methods=['GET','POST'])

# Table reload from table_view
app.add_url_rule(f"/table<int:index>/reload",
                 view_func=table_reload, methods=['GET','POST'])

# Table end
app.add_url_rule(f"/table<int:index>/end",
                 view_func=table_end, methods=['GET','POST'])

## Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    return response

## Allows to run the app/webpage as usual python scripts
if __name__ == "__main__":
    app.run(debug=True)