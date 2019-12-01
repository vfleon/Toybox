from toybox.interventions.amidar import *
import random
#import json
import itertools 

import numpy as np

"""An API for interventions on Amidar."""

mvmt_protocols = ['EnemyLookupAI', 'EnemyPerimeterAI', 'EnemyAmidarMvmt', 'EnemyTargetPlayer', 'EnemyRandomMvmt']
generative_support = ['player_start']

class AmidarGenerative(AmidarIntervention):

    def __init__(self, tb, game_name='amidar'):
        # check that the simulation in tb matches the game name.
        AmidarIntervention.__init__(self, tb, game_name)

    def set_partial_config(self, fname): 
        import os

        if os.path.isfile(fname): 
            with open(fname) as f:
                data = json.load(f)
        self.dirty_config = True
        for k in data.keys(): 
            if k in self.config.keys():
                self.config[k] = data[k]

            elif k == "randomize": 
                self.config[k] = data[k]
                self.set_procedure(data[k])

        # assert for all random elements: choice and weight lists in config are defined 
        for var in self.config['randomize'].keys(): 
        	assert len(self.config[var+'.choices']) > 0

        self.resample_state()                
        print(self.config)


    def set_procedure(self, data):
        # load randomized variable choices 
        # assign to game generator 
        for var in [k for k in data.keys() if k in generative_support]:
            if var == 'player_start':      
                var_list, weighted_choice = self.unload_starting_position(data[var])
                # unload choices 
                self.config[var+".choices"] = var_list
                # unload weights
                self.config[var+".weights"] = weighted_choice if weighted_choice is not None else []
               
        for var in [k for k in data.keys() if not k in generative_support]:    
            print('Randomizer not supported:', var)


    def tile_wrapper(self, y, x): 
        return {'ty': y, 'tx': x}


    def unload_starting_position(self, data): 
        correct_bug_refresh = False
        if "player_start" in data.keys():
            correct_bug_refresh = True 
        if "randomize" in self.config.keys(): 
            if "player_start" in self.config["randomize"].keys() and "default_board_bugs" not in data.keys(): 
                    correct_bug_refresh = True 
        if correct_bug_refresh: 
        	# if default_board_bugs has not been set elsewhere in config, set to False here and reset paint
            self.config["default_board_bugs"] = False
            if 'no_chase' in self.config.keys(): 
                chickens = self.config['no_chase']
            else: 
                chickens = False
            self.empty_board_paint_config(chickens)

        load_keys = [k for k in data.keys()]
        var_list = []
        for load_protocol in load_keys: 
            if load_protocol == 'rect_range': 
                pass
                #var_list.extend(list(itertools.product(data[load_protocol]['y1']:data[load_protocol]['y2'],data[load_protocol]['x1']:data[load_protocol]['x2'])))
            if load_protocol == 'comb_list':
                var_list.extend(list(itertools.product(data[load_protocol]["xrange"],data[load_protocol]["yrange"])))
            if load_protocol == 'zip_list': 
                ylist = np.arange(data[load_protocol]['y1'],data[load_protocol]['y2'])
                xlist = np.arange(data[load_protocol]['x1'],data[load_protocol]['x2'])
                if len(ylist) == len(xlist): 
                    var_list.extend(list(set(zip(ylist,xlist))))
                else: 
                    print("Invalid coordinate input: ", load_protocol, data[load_protocol])

        assert len(var_list) > 0

        # format list to correct dictionary form (input as y, x)
        var_list = [self.tile_wrapper(v[1],v[0]) for v in var_list]

        # filter out inappropriate player positions
        var_list = [v for v in var_list if self.check_is_tile(v)]
        assert len(var_list) > 0

        return var_list, None


    def resample_state(self): 
        for var in self.config["randomize"]: 
            if self.config[var+".weights"] != []: 
                print("weights:", self.config[var+".weights"])
                self.config[var] = np.random.choice(self.config[var+".choices"], p=self.config[var+".weights"])
            else: 
                self.config[var] = np.random.choice(self.config[var+".choices"])



if __name__ == "__main__":
    import argparse 

    parser = argparse.ArgumentParser(description='test Amidar generative fns')
    parser.add_argument('--partial_config', type=str, default="null")
    parser.add_argument('--save_json', type=bool, default=False)

    pre_img_path = "pre_img.jpg"
    post_img_path = "post_img.jpg"

    args = parser.parse_args()

    with Toybox('amidar') as tb:
        state = tb.to_state_json()
        config = tb.config_to_json()

        test_config_fname = "toybox/toybox/generative/amidar_quick_config.json"
        with AmidarGenerative(tb) as rogue: 
            rogue.set_partial_config(test_config_fname)

        if args.save_json:
            # save a sample starting state and config
            with open('toybox/toybox/interventions/defaults/amidar_state_trail.json', 'w') as outfile:
                json.dump(state, outfile)

            with open('toybox/toybox/interventions/defaults/amidar_config_trial.json', 'w') as outfile:
                json.dump(config, outfile)



        if args.save_tile_images: 
            for ty in range(len(state['board']['tiles'])):
                for tx in range(len(state['board']['tiles'][ty])):
                    tile_pos = {'tx':tx, 'ty':ty}

                    with AmidarIntervention(tb) as intervention:
                        is_tile = intervention.check_is_tile(tile_pos)

                    if is_tile:
                        with AmidarIntervention(tb) as intervention:
                                intervention.set_tile_paint(tile_pos)

                        fname = 'tile_tx_'+str(tx)+'_ty_'+str(ty)+'.jpg'
                        tb.save_frame_image(fname, grayscale=False)

                        with AmidarIntervention(tb) as intervention: 
                            intervention.set_tile_paint(tile_pos, False)