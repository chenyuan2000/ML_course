"""
The template of the script for the machine learning process in game pingpong
"""

# Import the necessary modules and classes
from mlgame.communication import ml as comm
import pickle
import numpy as np
from os import path

def ml_loop(side: str):
    """
    The main loop for the machine learning process

    The `side` parameter can be used for switch the code for either of both sides,
    so you can write the code for both sides in the same script. Such as:
    ```python
    if side == "1P":
        ml_loop_for_1P()
    else:
        ml_loop_for_2P()
    ```

    @param side The side which this script is executed for. Either "1P" or "2P".
    """

    # === Here is the execution order of the loop === #
    # 1. Put the initialization code here
    ball_served = False
    if side == "1P":
        filename = path.join(path.dirname(__file__), 'save', 'clf_SVMClassification_BallAndDirection.pickle')
    else:
        filename = path.join(path.dirname(__file__), 'save', 'clf_SVMClassification_BallAndDirection_2.pickle')
    with open(filename, 'rb') as file:
        clf = pickle.load(file) 

    def get_direction(SpeedX, SpeedY):
        if(SpeedX>=0 and SpeedY>=0):
            return 0
        elif(SpeedX>0 and SpeedY<0):
            return 1
        elif(SpeedX<0 and SpeedY>0):
            return 2
        elif(SpeedX<0 and SpeedY<0):
            return 3
    # 2. Inform the game process that ml process is ready
    comm.ml_ready()

    # 3. Start an endless loop
    while True:
        # 3.1. Receive the scene information sent from the game process
        scene_info = comm.recv_from_game()
        feature = []
        #feature.append(scene_info['frame'])
        feature.append(scene_info['ball'][0])
        feature.append(scene_info['ball'][1])
        feature.append(scene_info['ball_speed'][0])
        feature.append(scene_info['ball_speed'][1])
        feature.append(scene_info['blocker'][0])
        #feature.append(scene_info['blocker'][1])
        feature.append(scene_info['platform_1P'][0])
        #feature.append(scene_info['platform_1P'][1])
        feature.append(scene_info['platform_2P'][0])
        #feature.append(scene_info['platform_2P'][1])

        feature.append(get_direction(feature[2],feature[3]))
        
        feature = np.array(feature)
        feature = feature.reshape((-1,8))

        # 3.2. If either of two sides wins the game, do the updating or
        #      resetting stuff and inform the game process when the ml process
        #      is ready.
        if scene_info["status"] != "GAME_ALIVE":
            # Do some updating or resetting stuff
            ball_served = False

            # 3.2.1 Inform the game process that
            #       the ml process is ready for the next round
            comm.ml_ready()
            continue

        # 3.3 Put the code here to handle the scene information

        # 3.4 Send the instruction for this frame to the game process
        if not ball_served:
            comm.send_to_game({"frame": scene_info["frame"], "command": "SERVE_TO_LEFT"})
            ball_served = True
        else:
            y = clf.predict(feature)
            if y == 0:
                comm.send_to_game({"frame": scene_info["frame"], "command": "NONE"})
            elif y == 1:                    
                comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_LEFT"})
            elif y == 2:
                comm.send_to_game({"frame": scene_info["frame"], "command": "MOVE_RIGHT"})
