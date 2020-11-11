#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Oct 10 14:52:28 2020

@author: luke
"""

import pandas as pd
import os
import numpy as np
import datetime as dt

pk='pk'
sk='sk'
fltr='fltr'
skids=['MEALPLAN','USER','SESSION','RECIPES','INGREDIENTS']
adddict={'type':'personal',
         'numberOfPeople': 1,
         'dietType': 'regular',
         'portionSizes': 'medium',
         'planDuration':'weekly',
         'freezeIngredients': True,
         'ingredientFlexibility': False,
         'otherOptions':[],
         'dietaryRequirement':[]
         }

dayopts={'dayOptions':[
    {'day':1, 
     'mealTypes': [{'mealType':'breakfast',
                    'cookingTimeLimit': 30},
                   {'mealType':'lunch',
                    'cookingTimeLimit':60}
                   ]
     }]}
f={}
adddict['dayOptions']=dayopts['dayOptions']
f[('luke#lukemenzies', 'MEALPLAN')]=adddict

key=('luke#lukemenzies', 'MEALPLAN')
choices=f[key]
choices['type']
#ops=options()

    
#add=pd.concat((add,pd.DataFrame.from_dict(f,orient='index')),axis=1)


class options():
    def __init__(self, **kwargs):
        fvars={'types' : ['personal','group'],
               'typeNumbers' : [1,2,3,4,5],
               'mealTypes' : ['breakfast','lunch','dinner','tupperware'],
               'days': [1,2,3,4,5,6,7],
               'dietTypes' : ['regular','vegetarian',
                             'vegan','keto',
                             'atkins','pescaterian'],
               'portionSizes' : ['small','medium','large','human_dustbin'],
               'planDurations' : ['five_days','weekly','fortnightly','monthly'],
               'cookingTimes' : [30,60,120,240],
               'otherOptions' : ['no_bread','no_pasta',
                                 'light_breakfast','light_lunch',
                                 'light_dinner','no_pork',
                                 'no_beef'
                                 ],
               'dietaryRequirements' : ['nut','lactose','shellfish',
                                        'gluten','everything']
               }
        fvars.update(kwargs)
        self.options=fvars        
        
    
class database(options):
    def __init__(self,name='ScranPlanDatabase',path='./',**kwargs):
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
        if os.path.exists(filename):
            self.database=self.load(filename)
        else:
            ind=pd.MultiIndex.from_arrays([[],[]],names=(fvars['index']))
            self.database=pd.DataFrame([],columns=fvars['columns'],index=ind)
            self.database.columns.name=fvars['name']
            
    def add_user(self,username):
        status=True
        key=username,'USER'
        if self.check_exists(key):
            status=False
        else:
            ind=pd.MultiIndex.from_arrays([[username],['USER']],names=(self.index))
            add=pd.DataFrame([np.nan],columns=self.columns,index=ind)
            add['timestamp']=dt.datetime.now()
            self.database=self.database.append(add)
            self.database.columns.name=self.databasename
        return status
    
    def add_mealplan(self,username,mealplanname,choices=None):
        status=True
        name='{}#{}'.format(mealplanname,username)
        key=name,'MEALPLAN'
        if self.check_exists(key):
            status=False
        else:
            ind=pd.MultiIndex.from_arrays([[name],['MEALPLAN']],names=(self.index))
            add=pd.DataFrame([mealplanname],columns=self.columns,index=ind)
            add['timestamp']=dt.datetime.now()
            self.database=self.database.append(add)
            self.database.columns.name=self.databasename    
        if choices is not None:
            self.check_selection(choices)
            add=pd.DataFrame.from_dict({key:choices},orient='index')
            add.index.names=self.database.index.names
            newdb=self.database.join(add)
            self.database=newdb
        return status

    def check_exists(self,key):
        try:
            self.database.loc[key]
            return True
        except KeyError:
            return False
        
    def check_selection(self,choices):
        if choices['type'] in self.options['types']==False:
            raise TypeError
        if choices['type']=='group':
            if choices['numberOfPeople'] in self.options['typeNumbers']==False:
                raise TypeError    
        day_options=choices['dayOptions']
        for day in day_options:
            if day['day'] in self.options['days']==False:
                raise TypeError
            for meal in day['mealTypes']:
                if meal['mealType'] in self.options['mealTypes']==False:
                    raise TypeError
                if meal['cookingTimeLimit'] in self.options['cookingTimes']==False:   
                    raise TypeError                    
        if choices['dietType'] in self.options['dietTypes']==False:
            raise TypeError  
        if choices['portionSizes'] in self.options['portionSizes']==False:
            raise TypeError     
        if choices['dietType'] in self.options['dietTypes']==False:
            raise TypeError  
        if choices['planDuration'] in self.options['planDurations']==False:
            raise TypeError   
        if all([elem in self.options['otherOptions'] for elem in choices['otherOptions']])==False:
            raise TypeError      
        if all([elem in self.options['dietaryRequirements'] for elem in choices['dietaryRequirement']])==False:
            raise TypeError 
        
    def load(self,path):
        data=pd.read_csv(path,index_col=self.index,sep='~')
        return data
    
    def save(self,path):
        self.database.to_csv(path,sep='~')
        
adddict={'type':'personal',
         'numberOfPeople': 1,
         'dietType': 'regular',
         'portionSizes': 'medium',
         'planDuration':'weekly',
         'freezeIngredients': True,
         'ingredientFlexibility': False,
         'otherOptions':[],
         'dietaryRequirement':[]
         }

dayopts={'dayOptions':[
    {'day':1, 
     'mealTypes': [{'mealType':'breakfast',
                    'cookingTimeLimit': 30},
                   {'mealType':'lunch',
                    'cookingTimeLimit':60}
                   ]
     }]}
f={}
adddict['dayOptions']=dayopts['dayOptions']
f[('luke#lukemenzies', 'MEALPLAN')]=adddict

key=('luke#lukemenzies', 'MEALPLAN')
choices=f[key]
choices['type']

