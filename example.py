# -*- coding: utf-8 -*-

import lazygantt as lg
import os

PATH_MINIMAL_GANTT = os.path.join(os.path.curdir, 'files', 'minimal_gantt.csv')
PATH_GANTT = os.path.join(os.path.curdir, 'files', 'gantt.csv')
PATH_CONFIG = os.path.join(os.path.curdir, 'files', 'config.yaml')

def default_gantt():
    """Creates a generic gantt chart fully from default values and saves
    it to hard disc
    """
    
    myGenericGantt = lg.LazyGantt()
    myGenericGantt.plot()

def minimal_gantt_with_default_visuals():
    """Creates gantt chart from csv file with minimal number of columns
    """
    
    myGantt = lg.LazyGantt.load_data(PATH_MINIMAL_GANTT)
    print("The following data columns are processed: ", myGantt.ALL_COLUMNS)
    print("The following data columns are mandadory and throw exceptions, " \
          "if they are not part of the data: ", myGantt.MANDATORY_COLUMNS)
    myGantt.plot()

def minimal_gantt_with_default_visuals_and_milestones():
    """Creates gantt chart from csv file with minimal number of columns and
    milestones created from list
    """
    
    milestones = [6, 14, 20, 26, 33, 42, 67]
    myGantt = lg.LazyGantt.load_data(PATH_MINIMAL_GANTT, milestones=milestones)
    myGantt.plot()
    
def gantt_with_default_visuals():
    """Creates gantt chart from csv with extended number of columns and rows
    """
    
    myGantt = lg.LazyGantt.load_data(PATH_GANTT)
    myGantt.plot()

def gantt_with_configurated_visuals():
    """Creates gantt chart from csv with extended number of columns and rowts
    and appearance from configuration file
    """
    
    milestones = [-10, 12, 26, 33, 40]
    myGantt = lg.LazyGantt.load_data(PATH_GANTT, milestones)
    myGantt.load_config(PATH_CONFIG)
    myGantt.plot()

def main():
    # default_gantt()
    # minimal_gantt_with_default_visuals()
    minimal_gantt_with_default_visuals_and_milestones()
    # gantt_with_default_visuals()
    # gantt_with_configurated_visuals()

if __name__ == '__main__':
    main()