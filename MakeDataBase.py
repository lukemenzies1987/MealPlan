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
        self.droplist=['fltr','timestamp','updated_timestamp']
        if os.path.exists(filename):
            self.database=self.load(filename)
            
        else:
            ind=pd.MultiIndex.from_arrays([[],[]],names=(fvars['index']))
            self.database=pd.DataFrame([],columns=fvars['columns'],index=ind)
            self.database.columns.name=fvars['name']
            self.save(filename)
            
    def add_user(self,username):
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
        try:
            self.database.loc[key]
            return True
        except KeyError:
            return False
        
    def check_selection(self,choices):
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

