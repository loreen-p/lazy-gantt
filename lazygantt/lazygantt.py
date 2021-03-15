# -*- coding: utf-8 -*-
"""
Created on Thu Mar  4 10:25:39 2021

@author: Loreen
"""
import pandas as pd
import numpy as np
from .visuals import Chart

class LazyGantt(object):
    """A class used to represent data characteristics of a Gantt Chart
    
    Attributes
    ----------
    no_months : int
        number of total months of the project
    no_packages : int
        number of work packages within the project
    no_phases : int
        number of work phases within the project, 
        may be set to None if no phase data was offered during file loading
    packages : array_like
        array that holds starting and ending months of work packages
    phases : array_like
        array that holds starting and ending months of phases,
        may be set to None if no phase data was offered during file loading
    milestones : list
        list of integers after how many months milestones occur
    chart : Chart class
        instance of Chart class to handle plotting
    
    """
    
    # mapper directory to more easily adapt code for changing
    # column naming in source csv file
    # dict.values() are column names in csv file, dict.keys() are used in 
    #  _fill_from_csv to update class attributes
    VARIABLE_MAPPER = {'start': 'start',
                       'duration': 'length',
                       'phase_number': 'phase'} 
    ALL_COLUMNS = list(VARIABLE_MAPPER.keys())
    MANDATORY_COLUMNS = ['start', 'duration']

    def __init__(self, data=None, milestones=None):
        """
        Parameters
        ----------
            data : pandas Dataframe, optional
                data for creation of a Gantt chart containing at least columns
                as stated in MANDATORY_COLUMNS, or, also optional columns with
                naming scheme as stated in ALL_COLUMNS.
                The default is None.
        
        The following columns in the data are used for further processing:
            "start":
                start of work packages, in relative months from beginning
                of the project, starting from month 0.
                Example: 8, for a package starting in month 8 of the project
            "duration": 
                duration of work packages in months
                Example: 3, for a package lasting 3 months
            "phase_number": 
                Ascending number from 1 to n, stated for each work package. 
                Example: 2, for phase 2.
                Optional: If column is not included in csv file or contains 
                only one phase, the columns is processed further.
                
        Example content of csv file:
                start  duration  phase_number
            0       0         3             1
            1       3         6             1
            2       4        17             1
            3       5         3             1
            4       6        14             2
            5       8         4             2
            6      12         9             3
            7      16         9             3
                        [...]
            16     44         3             7
            17     46         2             7
        """
        self.no_months = 24
        self.no_packages = 6
        self.no_phases = 3
        # array with shape no_packages x no_months
        self.packages = np.array([
                        [ 0 ,3],
                        [ 3, 7],
                        [ 5,12],
                        [12,18],
                        [17,24],
                        [19,24]], dtype=np.int)
        # array with shape no_phases x no_months
        self.phases = np.array([
                        [ 0 ,6],
                        [ 6,16],
                        [16,24]], dtype=np.int)
        self.milestones = np.array(milestones) if milestones is not None \
                                            else np.array([5, 8, 14, 19, 22])
        self.chart = Chart()
        
        if data is not None:
            self._fill_from_csv(data)
            if milestones is not None:
                self._filter_milestones()
        
    @classmethod
    def load_data(cls, filepath, milestones=None, sep=";"):
        """Loads a csv file
        
        Parameters
        ----------
        filepath : str, path object or file-like object
            name and path to file to load
        milestones : list
            list of integers after how many months milestones should be plotted
        sep : str, optional
            delimiter that separates columns in csv file. The default is ";".

        Returns
        -------
        data : numpy Dataframe
            data necessary for creation of a Gantt chart
        """
        data = pd.read_csv(filepath, sep=sep, engine='python')
        return cls(data, milestones)
    
    def load_config(self, filepath):
        """Loads a configuration file
        
        Loads a configuration file for adapting visual appearance and 
        language of Gantt chart

        Parameters
        ----------
        filepath : str, path object or file-like object
            name and path to file to load
        """
        
        self.chart.load_config(filepath)
        
    def plot(self):
        """Plots data
        
        Prepares array-like data for plotting and passes data for plotting
        """
        packages = self._to_boolean_array(self.packages, self.no_months)
        phases = self._to_boolean_array(self.phases, self.no_months)
        self.chart.plot_gantt(packages, phases, self.milestones)

    def _fill_from_csv(self, data):
        """Fills class variables from data parsed from csv file
        
        Trims data, ensures correct data types, and updates class 
        variables from csv file

        Parameters
        ----------
        data : pandas Dataframe, optional
            Data for creation of a Gantt chart containing at least columns
            as stated in MANDATORY_COLUMNS, or, also optional columns with
            naming scheme as stated in ALL_COLUMNS.
        """
        
        ## filtering data columns
        myColumnChecker = DataColumnChecker(
                                data=data,
                                target_columns = self.ALL_COLUMNS,
                                mandatory_columns=self.MANDATORY_COLUMNS)
        filtered_columns = myColumnChecker.get_valid_columns()
        
        # key_mapper ensures that the correct data column is accessed,
        # without the need to know here the exact column name, since it is 
        # generated from filtered columns and static VARIABLE_MAPPER
        key_mapper = {}
        for col in filtered_columns:
            key_mapper = self._build_key_mapper(key_mapper, col)

        ## filtering data rows
        # delete cells where no starting month is stated (NAN values)
        # to remove rows without package data
        nan_rows = data[data[key_mapper['start']].isnull()].index.values
        data.drop(nan_rows, inplace=True)

        ## datatype conversion
        for k in key_mapper.keys():
            data[key_mapper[k]] = data[key_mapper[k]].astype('int32')
        
        ## total duration
        # not explicitely stated and not straightforward to calculate due to 
        # the possibility for overlapping packages: 
        # compose from last package plus the duration of this last package
        last_package_start = data[key_mapper['start']].max()
        last_package_duration = data.at[data[key_mapper['start']].idxmax(),
                                        key_mapper['length']]
        self.no_months = last_package_start + last_package_duration
        
        ## packages
        # only possible with sufficient cleaning
        self.no_packages = data.index.max()
        packages_start = data[key_mapper['start']].values[:]
        packages_duration = data[key_mapper['length']].values[:]
        self.packages = np.asarray((packages_start,
                                   packages_start+packages_duration)).T
        
        ## phases
        if 'phase' not in key_mapper:
            self.no_phases = None
            self.phases = None
        else:
            # phases column contains more than 1 number (i.e. phase)?
            if len(data[key_mapper['phase']].unique()) > 1:
                data[key_mapper[k]] = data[key_mapper[k]].astype('int32')
                self.no_phases = data[key_mapper['phase']].max()
                self.phases = self._compose_phases(
                                        data[key_mapper['phase']],
                                        data[key_mapper['start']],
                                        data[key_mapper['length']])
    
    def _build_key_mapper(self, key_mapper, string):
        """Builds a mapping dictionary to access data column names
        
        Builds a dictionary that data column names from input data to strings
        taken from static VARIABLE_MAPPER for accessing these columns. 
        Simplifies future code adaptions, if names of data columns will change. 
        Or, may be offered to the users to control the mapping by themselves.

        Parameters
        ----------
        key_mapper : dict
            dictionary with access string as keys and data column names as
            values
        string : str
            data column name

        Returns
        -------
        key_mapper : dict
            dictionary with access string as keys and data column names as
            values

        """
        if string in self.VARIABLE_MAPPER.keys():
            key_mapper[self.VARIABLE_MAPPER[string]] = string
        return key_mapper
    
    def _compose_phases(self, 
                        phases_assigned,
                        months_started,
                        months_lasting):
        """
        Compose phases array in format of
        arr = [[s1, e1],[s2, e2], ... ,[s(n-1), e(n-1)],[s(n), e(n)]]
        with s and e denoting starting and ending months of phases, 
        respectively.
        
        The difficulty lies in recognizing the change in phases, 
        collecting all associated packages per phase, and processing the 
        time parameters of the associated packages so that the starting and 
        ending month of all phases can be calculated.
        
        Phases are composed as in the following:
        (a) Search for changes in phases' assigned numbering by using forward 
        differentiation and save indices of phase changes.
        (b) Re-use indices to assemble starting and ending months of phases:
            (1) starting months: collect start values of all first 
                included packages per phase
            (2) ending months: collect start values of all last included 
                packages per phase and add their values for duration
        
        Parameters
        ----------
        phases_assigned
            Pandas series holding phase numbers
        months_started
            Pandas series holding starting months of packages
        months_lasting
            Pandas series holding duration of packages
        
        Returns
        -------
        arr : array-like
            array in shape of number of phases x 2 that holds starting and
            ending month of each phase
        
        Example:
        >>> print(phases_assigned.values[:])
        [1 1 1 1 2 2 3 3 4 4 5 5 5 5 6 6 7 7]
        >>> print(months_started.values[:])
        [ 0  3  4  5  6  8 12 16 20 24 27 28 32 35 38 41 44 46]
        >>> print(months_lasting.values[:])
        [ 3  6 17  3 14  4  9  9  5  5 14  5  8  5  6  4  3  2]
        >>> arr = self._compose_phases
        >>> print(arr)
            [[ 0 20]
             [ 6 21]
             [12 25]
             [20 41]
             [27 44]
             [38 47]
             [44 48]]
        
        """
        
        phases = np.zeros((self.no_phases, 2), dtype=int)

        # find changes of numbering in phases
        idx_phase_change = phases_assigned.diff()[
                                phases_assigned.diff() != 0].index.values[:]
        # fill phase starts
        phases[:, 0] = months_started[idx_phase_change].values
        # fill phase lengths, except for last phase, which is closed by hand
        phases[:-1, 1] = (months_started[idx_phase_change[1:]].values+
                          months_lasting[idx_phase_change[1:]].values)
        # close last phase with total amount of available months
        phases[-1, 1] = self.no_months
        return phases

    def _filter_milestones(self):
        """Filters milestones that exceed project duration or are negative
        """
        too_small = (self.milestones < 0)
        if np.sum(too_small) > 0:
            print("Values for milestones are negative: {}"
                  .format(self.milestones[too_small]))
            ix_huge_enough = np.nonzero(~too_small)
            self.milestones = self.milestones[ix_huge_enough]
        
        too_big = (self.milestones > self.no_months)
        if np.sum(too_big) > 0:
            print("Values for milestones exceed total length of project of " \
                  "{max} and are filtered: {values}" .format(
                      max=self.no_months, 
                      values= self.milestones[np.nonzero(too_big)]))
            # get indicies where condition too_big is not True
            ix_small_enough = np.nonzero(~too_big)
            self.milestones = self.milestones[ix_small_enough]

    def _to_boolean_array(self, arr, x_range):
        """Converts array to matrix in shape of len(arr) X x_range
        
        Converts array to matrix in shape of len(arr) X x_range
        
        Parameters
        ----------
        arr : array-like
            Array in shape of number of temporal representatives (packages, 
            phases) x 2 (for starting and ending point in time)
            Example: 7 packages, 12 months project duration -> shape 7 x 2
        x_range : int
            The number of columns of the new array.

        Returns
        -------
        boolean_arr : array-like
            Array in shape of number of temporal representatives (packages,
            phases) x number of total months,
            holding TRUE values, where packages or phases are present
            Example: 7 packages, 12 months project duration -> shape 7 x 12
        
        """
        
        if arr is None:
            pass
        else:
            y_range = len(arr)
            boolean_arr = np.reshape(np.full(y_range*x_range, 
                                    fill_value=False, dtype=bool),
                                    newshape=(y_range,self.no_months))
            for i in range(len(arr)):
                boolean_arr[i, arr[i, 0]:arr[i, 1]] = True
            
            return boolean_arr


class DataColumnChecker(object):
    """A class for checking for valid dataframe columns
    
    A class for checking for valid dataframe columns that covers the existence,
    content and type of columns. Valid column names are hold in target_columns.
    Differentiates between optional and mandatory columns: If an optional
    column is not valid, a simple statement is printed. If a mandatory column 
    is not valid, an exception is thrown.
    
    Attributes
    ----------
    data : pandas dataframe
        data for creation of a Gantt chart containing different data columns
    target_columns : list of str
        list of column names which are valid
    mandatory_columns : list of str
        list of column names which are mandatory to be valid. If they are not
        valid, an exception is thrown.
        Optional.
    conditions : dict
        dictionary that holds routines to check for valid columns
    
    """
    
    def __init__(self, 
                 data, 
                 target_columns,
                 mandatory_columns=None):
        # filter for empty list
        if not target_columns:
            raise Exception("Empty target_columns! No filtering possible!")
        self.target_columns = target_columns
        self.mandatory_columns = mandatory_columns if mandatory_columns \
                                 is not None else list()
        self.conditions = {'existent_column': self._check_existence,
                           'content_in_column': self._check_content,
                           'string_in_column': self._check_for_strings}
        self._filter_for_valid_columns(data)
    
    def get_valid_columns(self):
        """Returns valid columns after filtering

        Returns
        -------
        Return value: list
            list with names of valid columns

        """
        return self.target_columns
    
    def _filter_for_valid_columns(self, data):
        """Filters target columns for existent and valid ones from input data
        
        Processes input data for existence, content and valid type of column
        data. Invalid columns are ignored for further processing.
        
        Parameters
        ----------
        data : pandas dataframe
            data for creation of a Gantt chart containing data columns

        Raises
        ------
        Exception
            If mandatory columns cannot be processed, since they are not valid.
        
        """
        
        for column in self.target_columns:
            for key, value in self.conditions.items():
                # processes cascade of conditions
                is_valid, message = self.conditions[key](column, data)
                if is_valid:
                    pass
                else:
                    # throw exception only if there is a problem with mandatory
                    # columns
                    if column in self.mandatory_columns:
                        raise Exception(
                            "Mandatory column cannot be processed! " \
                            "{}" .format(message))
                        
                    # remove all optional columns that did not fulfilled all
                    # conditions
                    self.target_columns.remove(column)
                    print(message)
                    break

    def _check_existence(self, column, data):
        """Checks for the existence of a column within a dataframe
        
        Parameters
        ----------
        column : str
            name of the column
        data : pandas dataframe
            table-like data

        Returns
        -------
        the return value : bool
            True for success, False otherwise.
        message : str
            description of result of validation
            
        """
        if column in data.columns:
            return (True, "Column '{}' exists." .format(column))
        else:
            message = ("Column '{}' is missing in your input data!" .format(
                                                                    column))
            return (False, message)
    
    def _check_content(self, column, data):
        """Checks for non-empty column within dataframe

        Parameters
        ----------
        column : str
            name of the column
        data : pandas dataframe
            table-like data

        Returns
        -------
        the return value : bool
            True for success, False otherwise.
        message : str
            description of result of validation 

        """
        if not data[column].isnull().values.all():
            return (True, "Column '{}' contains content." .format(column))
        else:
            message = ("Column '{}' is ignored, since it is empty!" .format(
                                                                    column))
            return (False, message)
    
    def _check_for_strings(self, column, data):
        """Checks for the occurence of strings in column within dataframe

        Parameters
        ----------
        column : str
            name of the column
        data : pandas dataframe
            table-like data

        Returns
        -------
        the return value : bool
            True for success, False otherwise.
        message : str
            description of result of validation 

        """
        from pandas.api.types import is_string_dtype
        if not is_string_dtype(data[column]):
            return (True, "Column '{}' does not contain text." .format(column))
        else:
            message = ("Column '{}' is ignored, since it holds text instead " \
                  "of numeric data!" .format(column))
            return (False, message)