#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 10 14:52:28 2020

The routines in the script have been built for use within the ScranPlan API.
They are intended for keeping records of users and mealplans. 

@author: Luke Menzies
"""

import pandas as pd
import os
import numpy as np
import datetime as dt

pk='pk'
sk='sk'
fltr='fltr'
skids=['MEALPLAN','USER','SESSION','RECIPES','INGREDIENTS']

class options():
    def __init__(self, **kwargs):
        """
        This contains the allowed options when generating or editing a meal 
        plan. These are used when checking options sent through via the API.

        Parameters
        ----------
        **kwargs : See below for list of options. 
        Returns
        -------
        None.

        """
        fvars={'types' : ['personal','group'], #Diet type
               'typeNumbers' : [1,2,3,4,5], #Number of peoople the meal plan is for
               'mealTypes' : ['breakfast','lunch','dinner','tupperware'], #Allowed meal types
               'days': [1,2,3,4,5,6,7], #Which days of the week is the plan for.
               'dietTypes' : ['regular','vegetarian',
                             'vegan','keto',
                             'atkins','pescaterian'], #Diet Type
               'portionSizes' : ['small','medium','large','human_dustbin'], #Portion sizes
               'planDurations' : ['five_days','weekly','fortnightly','monthly'], #The period to optimise over
               'cookingTimes' : [30,60,120,240], #Rough maximum cooking time for any recipe.
               'otherOptions' : ['no_bread','no_pasta',
                                 'light_breakfast','light_lunch',
                                 'light_dinner','no_pork',
                                 'no_beef'
                                 ], #Other optoins
               'dietaryRequirements' : ['nut','lactose','shellfish',
                                        'gluten','everything'] #If anyone has allergies
               }
        fvars.update(kwargs)
        self.options=fvars        
        
    
class database(options):
    def __init__(self,name='ScranPlanDatabase',path='./',**kwargs):
        """
        This class houses the routines used to generate, delete and modify
        usernames and mealplans. 

        Parameters
        ----------
        name : str, optional
            This is passed name for the main file containing all the records. 
            Note the suffix is missing, since is it set later to csv. Additionally
            if no file exists, the routine automatically makes a blank file. 
            The default is 'ScranPlanDatabase'. 
        path : str, optional
            path to main file, that is joined to the name. The default is './'.
        **kwargs : dict
            contains dataframe components.

        Returns
        -------
        None.

        """
        fvars={'index': [pk,sk], 'columns': [fltr], 'name' : 'ScranPlan'}
        fvars.update(kwargs)
        super().__init__()
        self.name=name
        self.databasename=fvars['name']
        filename='{}.csv'.format(name)
        filename=os.path.join(path,filename)
        self.filename=filename
        self.columns=fvars['columns']
        self.index=fvars['index']
        self.droplist=['fltr','timestamp','updated_timestamp']
        if os.path.exists(filename):
            self.database=self.load(filename)
            
        else:
            ind=pd.MultiIndex.from_arrays([[],[]],names=(fvars['index']))
            self.database=pd.DataFrame([],columns=fvars['columns'],index=ind)
            self.database.columns.name=fvars['name']
            self.save(filename)
            
    def add_user(self,username):
        """
        This adda a new user to the database. It first checks to see if the user
        already exists within the database. 

        Parameters
        ----------
        username : str
            The name of the new user to be added.

        Returns
        -------
        dict
            Returns a message containing the status of the add call.

        """
        key=username,'USER'
        if self.check_exists(key):
            return {'status': False,
                    'message': 'User already exists'}
        else:
            ind=pd.MultiIndex.from_arrays([[username],['USER']],names=(self.index))
            add=pd.DataFrame([np.nan],columns=self.columns,index=ind)
            add['timestamp']=dt.datetime.now()
            self.database=self.database.append(add)
            self.database.columns.name=self.databasename
        return {'status': True,
                'message': 'Added user'}
    
    def add_mealplan(self,username,mealplanname,choices=None):
        """
        This adds a new mealplan for the passed username. It checks to see if
        the meal plan name already exists. 

        Parameters
        ----------
        username : str
            The username to associate the proposed meal plan with.
        mealplanname : str
            The meal plan name.
        choices : dist, optional
            This contains the selected options passed through the API. 
            The default is None.

        Returns
        -------
        dist
            Returns a message containing the status of the add meal plan call.

        """
        name='{}#{}'.format(mealplanname,username)
        key=name,'MEALPLAN'
        if self.check_exists(key):
            return {'status': False,
                    'message': 'Meal plan already exists'}
        else:
            ind=pd.MultiIndex.from_arrays([[name],['MEALPLAN']],names=(self.index))
            add=pd.DataFrame([mealplanname],columns=self.columns,index=ind)
            self.database=self.database.append(add)
            self.database.columns.name=self.databasename    
        if choices is not None:
            check=self.check_selection(choices)
            if check['status']:
                add=pd.DataFrame.from_dict({key:choices},orient='index')
                add['fltr']=mealplanname
                add['timestamp']=dt.datetime.now()
                add.index.names=self.database.index.names
                newdb=self.database.to_dict(orient='index')
                newdb.update(add.to_dict(orient='index'))
                self.database=pd.DataFrame.from_dict(newdb,orient='index')
                self.database.index.names=['pk','sk']
            else:
                return check
        return {'status': True,
                'message': 'Added meal plan'}

    def update_mealplan(self,username,mealplanname,choices=None):
        """
        This updates an existing meal plan with any modifications required as
        well as adding an updated timestamp to the database. It checks to see 
        if the record already exists. 

        Parameters
        ----------
        username : str
            The username to associate the proposed meal plan modifications with.
        mealplanname : str
            The name of the meal plan wishing to be modified.
        choices : dict, optional
            Contains the modification choices passed via the API. 
            The default is None.

        Returns
        -------
        dict
            Returns a message containing the status of the update meal plan call.

        """
        name='{}#{}'.format(mealplanname,username)
        key=name,'MEALPLAN'
        if self.check_exists(key):
            check=self.check_selection(choices)
            if check['status']:
                add=pd.DataFrame.from_dict({key:choices},orient='index')
                add.index.names=self.database.index.names
                add.index.names=['pk','sk']
                add['updated_timestamp']=dt.datetime.now()
                newdb=self.database.to_dict(orient='index')
                newdb.update(add.to_dict(orient='index'))
                self.database=pd.DataFrame.from_dict(newdb,orient='index')
                self.database.index.names=['pk','sk']
                return {'status': True,
                        'message': 'Successfully updated meal plan'}
            else:
                return check
        else:
            return {'status': False,
                    'message': 'Meal plan does not exist'}
        
    def get_mealplan_details(self,username,mealplanname):
        """
        This is used to find the details of any given meal plan. It checks if 
        the meal plan exists then returns the details. 

        Parameters
        ----------
        username : str
            The username associated with the meal plan being searched for.
        mealplanname : str
            Name of meal plan being searched for.

        Returns
        -------
        dict
            This contains the options of the selected meal plan.

        """
        key = ('{}#{}'.format(mealplanname,username),'MEALPLAN')
        if self.check_exists(key):
            select=self.database.loc[key]
            drop=[i for i in select.index if i in self.droplist]
            details=select.drop(drop).to_dict()
            return {'status': True,
                    'message': 'Found meal plan',
                    'details': details
                    }
        else:
            return {'status': False,
                    'message': 'Meal plan does not exist'
                    }          

    def delete_mealplan(self,username,mealplanname):
        """
        This deletes a meal plan from the records. 

        Parameters
        ----------
        username : str
            Username associated with the meal plan to be deleted.
        mealplanname : str
            Name of the meal plan that is to be deleted.

        Returns
        -------
        dict
            Returns a message containing the status of the meal plan deletion.

        """
        key = ('{}#{}'.format(mealplanname,username),'MEALPLAN')
        if self.check_exists(key):
            self.database.drop(key,inplace=True)
            return {'status': True,
                    'message': 'Deleted meal plan',
                    }
        else:
            return {'status': False,
                    'message': 'Meal plan does not exist'
                    } 
        
    def check_exists(self,key):
        """
        This checks the existance of an entry within the database using a passed
        key. 

        Parameters
        ----------
        key : Tuple
            Contains the key used in the database. This comprises the primary key
            pk and the secondary key sk

        Returns
        -------
        bool
            The bool says whether the entry exists or not.

        """
        try:
            self.database.loc[key]
            return True
        except KeyError:
            return False
        
    def check_selection(self,choices):
        """
        This is used to check the options for a meal plan that is passed via the 
        API. if there are options within the entries that are not allowed, it 
        will return a False status. 

        Parameters
        ----------
        choices : dict
            Contains the options for a meal plan, passed throught the API.

        Returns
        -------
        dict
            Returns a status message containing whether the options are valid 
            of not.

        """
        if (choices['type'] in self.options['types'])==False:
            return {'status': False,
                    'message': 'Incorrect choices type'}
        if choices['type']=='group':
            if (choices['numberOfPeople'] in self.options['typeNumbers'])==False:
                return {'status': False,
                    'message': 'Incorrect group type'}
        day_options=choices['dayOptions']
        for day in day_options:
            if (day['day'] in self.options['days'])==False:
                return {'status': False,
                        'message': 'Incorrect day type'}
            for cnt, meal in enumerate(day['mealTypes']):
                if (meal['mealType'] in self.options['mealTypes'])==False:
                    return {'status': False,
                            'message': 'Incorrect meal type at point {}'.format(cnt)}
                if (meal['cookingTimeLimit'] in self.options['cookingTimes'])==False:   
                    return {'status': False,
                            'message': 'Incorrect cooking time limit at point {}'.format(cnt)}                                   
        if (choices['dietType'] in self.options['dietTypes'])==False:
            return {'status': False,
                    'message': 'Incorrect diet type'}   
        if (choices['portionSizes'] in self.options['portionSizes'])==False:
            return {'status': False,
                    'message': 'Incorrect portion sizes'} 
        if (choices['planDuration'] in self.options['planDurations'])==False:
            return {'status': False,
                    'message': 'Incorrect plan duration'}     
        if all([elem in self.options['otherOptions'] for elem in choices['otherOptions']])==False:
            return {'status': False,
                    'message': 'Incorrect other options'} 
        if all([elem in self.options['dietaryRequirements'] for elem in choices['dietaryRequirement']])==False:
            return {'status': False,
                    'message': 'Incorrect dietary requirement options'}
        return {'status': True,
                'message': 'No problems with choices'}
        
    def load(self,path):
        """
        Loads data from the database file.

        Parameters
        ----------
        path : str
            path to database (including filename). This is self.filename in the 
            object.

        Returns
        -------
        None.

        """
        self.database=pd.read_csv(path,index_col=self.index,sep='~')
        return None
    
    def save(self,path):
        """
        This saves the modifications made to the database.

        Parameters
        ----------
        path : str
            path to database (including filename). This is self.filename in the 
            object.

        Returns
        -------
        None.

        """
        self.database.to_csv(path,sep='~')