# -*- coding: utf-8 -*-
"""
Created on Thu Mar 11 15:31:50 2021

@author: Loreen
"""
import yaml
import numpy as np

import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap
import matplotlib.colors as mcolors
from mpl_toolkits.axes_grid1 import ImageGrid

class Chart(object):
    """A class to plot charts
    
    A class to plot charts, currently only holding a Gantt chart. The
    appearance of the charts can be adapted via loading a configuration file.
    
    Attributes
    ----------
    colors : dict
        dictionary that holds color names known by matplotlib
    image : dict
        dictionary that holds image characteristics
    font: dict
        dictionary that holds font characteristics
    milestones : dict
        dictionary for plotting milestones
    labels: dict
        dictonary that hold mainly axis labels
    """
    
    def __init__(self, config=None):
        self.colors = {'primary': 'steelblue',
                       'secondary': 'yellowgreen',
                       'contrast': 'darkred',
                       'background': 'beige'}
        self.image = {'width': 25,
                      'height': 10,
                      'aspect': 1.,
                      'dpi': 150,
                      'format': 'png'}
        self.milestones = {'linewidth': 2.5}
        self.labels = {'package_abbr': 'WP',
                       'package_ylabel': 'Work Packages',
                       'milestones_abbr': 'MS',
                       'phase_abbr': 'P',
                       'phase_ylabel': 'Phases',
                       'xlabel': 'Months',
                       'xticks_steps': 2}
        self.font = {'fontsize': '16'}
        if config is not None:
            self._process_config(config)
    
    def load_config(self, filepath):
        """
        Loads configuration file

        Parameters
        ----------
        filepath : str, path object or file-like object
            name and path to file to load
        """
        
        config = yaml.safe_load(open(filepath))
        self._process_config(config)
        
    def _process_config(self, config):
        """Updates class variables with data from config file

        Parameters
        ----------
        config : dict
            dictionary that hold data from a yaml file

        """
        
        # test for colors following the naming conventions of matplotlib
        for k, v in config['colors'].items():
            try:
                mcolors.CSS4_COLORS[v]
            except KeyError:
                print("Color stated for '%s' does not exist! \
                      Choose color from: '%s'" % 
                      (k, list(mcolors.CSS4_COLORS.keys())))
            else:
                self.colors[k] = v
        
        self.image = config['image']
        self.font = config['font']
        self.milestones = config['milestones']
        self.labels = config['labels']
        
    def plot_gantt(self, main_slots, voluntary_slots=None, events=None):
        """Plots Gantt chart
        
        Parameters
        ----------
        main_slots : array-like
            array in shape of number of packages x number of total months,
            filled with True values when packages are present
        voluntary_slots : array-like, optional
            array in shape of number of phases x number of total months,
            filled with True values when phases are present
        events : list, optional
            list of integers after how many months event occured

        """
        
        ## font settings
        font = {'weight' : 'normal',
                'size'   : self.font['fontsize']}
        plt.rc('font', **font)
        
        ## label settings
        xlabel = self.labels['xlabel']
        xticks_steps = self.labels['xticks_steps']

        ## image settings
        fig = plt.figure(figsize=(self.image['width'],
                                  self.image['height']))
        aspect = self.image['aspect']
        
        # creates list of arguments for plotting function
        primary_slots = [main_slots, 
                   events,
                   'primary', 
                   self.labels['package_abbr'], 
                   self.labels['package_ylabel'], 
                   xlabel,
                   aspect,
                   xticks_steps]
        secondary_slots = [voluntary_slots, 
                     events,
                     'secondary', 
                     self.labels['phase_abbr'],
                     self.labels['phase_ylabel'], 
                     xlabel,
                     aspect,
                     xticks_steps]
        event_visuals = [events, 
                    'contrast', 
                    self.labels['milestones_abbr'],
                    self.milestones['linewidth']]
        
        # dynamically set number of subplots
        if voluntary_slots is not None:
            subplots = (2, 1)
        else:
            subplots = (1, 1)
        
        # create image grid with number of subplots
        axes = ImageGrid(fig, 
                         111,  # similar to subplot(111)
                         nrows_ncols=subplots,
                         axes_pad=0.1,  # pad between axes in inch
                         )
        
        # append axes object for correct plotting position
        if voluntary_slots is not None:
            primary_slots.append(axes[1])
            secondary_slots.append(axes[0])
            event_visuals.extend([True, axes[1]])
        else:
            primary_slots.append(axes[0])
        
        # pass plotting arguments to plot slots
        self._plot_slots(*primary_slots)
        self._plot_slots(*secondary_slots)
        self._plot_events(*event_visuals)
        # self._plot_events(**tertiary.append(False, axes[0]))
        
        ## image handling
        fig.savefig('gantt.'+self.image['format'], 
                    dpi=self.image['dpi'],
                    format=self.image['format'])
        # plt.close(fig)
    
    def _plot_events(self, 
                     events, 
                     color_key, 
                     label=None, 
                     linewidth=1.,
                     show_label=True, 
                     ax=None):
        """Plots event data, e.g. milestones

        Parameters
        ----------
        events : array-like
            array of shape number of events x month of occurence
        color_key : dict
            a dictionary with arguments to `matplotlib.Figure.colorbar`. 
            Optional.
        label : str
            prefix to plot numbers on milestones
        show_label : boolean, optional
            show event label as overlaid text boxed
        ax : matplotlib.axes.Axes
            a `matplotlib.axes.Axes` instance to which the slots are plotted.
            If not provided, use current axes or create a new one.
            Optional.
        """
        if events is None:
            return
        
        if not ax:
            ax = plt.gca()
            
        ymin, ymax = ax.get_ylim()
        ax.vlines(events-.5, ymin, ymax, 
                  self.colors[color_key], 
                  linewidth=linewidth)
        if show_label:
            for ix, event in enumerate(events):
                ax.text(event-.5, ymax, "MS "+str(ix+1), 
                        color=self.colors[color_key],
                        bbox={'fc':'white', 'pad':2})
    
    def _plot_slots(self, 
                    data,
                    events,
                    color_key,
                    slotlabel=None, 
                    ylabel=None, 
                    xlabel=None, 
                    aspect=1., 
                    xticks_steps=1,
                    ax=None):
        """Plots temporal interval data into a grid
    
        Parameters
        ----------
        data : array-like
            a 2D numpy array of shape number of representatives (e.g., phases) 
            x total number of time slots.
        color_key : dict
            A dictionary with arguments to `matplotlib.Figure.colorbar`. 
            Optional.
        slotlabel : str
            string suffix to number slots
        ylabel : str
            label for y axis
        xlabel : str
            label for x axis
        aspect : float
            the aspect ratio of the axes. It determines whether data pixels 
            are square which is the case for a value of 1.
            Optional.
        xticks_steps : int
            display every nth tick label on x-axis.
            Optional.
        events_linewidth : float
            
        ax : matplotlib.axes.Axes
            a `matplotlib.axes.Axes` instance to which the slots are plotted.
            If not provided, use current axes or create a new one.
            Optional.
        
        """
        if data is None:
            return
        
        if not ax:
            ax = plt.gca()

        x_max, y_max = data.shape[1], data.shape[0]
        
        ## coloring
        cell_color = self.colors[color_key]
        cmap = LinearSegmentedColormap.from_list(
                                    'mycmap', ['white', cell_color])
        
        ## plotting slots
        # plot packages as color-filled cells in image grid
        ax.imshow(data, 
                  cmap=cmap, interpolation='nearest',
                  vmin=0, vmax=1, origin='upper', aspect=aspect)
        
        ## plotting events
        # ymin, ymax = ax.get_ylim()
        # ax.vlines(events-.5, ymin, ymax, 
        #           colors=self.colors['contrast'], 
        #           linewidth=2.5)
        # for ix, event in enumerate(events):
        #     ax.text(event-.5, ymax, "MS "+str(ix+1), 
        #             bbox={'fc':'white', 'pad':2})
        
        ## text annotations
        pad_correction = 0.4
        text_positions = np.argmax(data, axis=1)
        for y, x in enumerate(text_positions):
            ax.text(x-pad_correction, y, 
                    slotlabel+str(y+1), 
                    va='center', ha='left')
        # axes annotations
        ax.set_ylabel(ylabel)
        ax.set_xlabel(xlabel)
        
        ## tick appearance
        # major ticks
        ax.set_xticks(np.arange(0, x_max, 1))
        ax.set_yticks([])
        # labels for major ticks
        ax.set_xticklabels(np.arange(1, x_max+1, 1))
        ax.set_yticklabels([])
        # minor ticks
        ax.set_xticks(np.arange(-.5, x_max, 1), minor=True)
        # hide selected tick labels
        if xticks_steps > 1:
            for label in ax.xaxis.get_ticklabels()[::xticks_steps]:
                label.set_visible(False)
        ax.set_yticks(np.arange(-.5, y_max, 1), minor=True)
        # gridlines based on minor ticks
        ax.grid(which='minor', color='gray', linestyle='-', linewidth=1)