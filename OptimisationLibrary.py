#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 11:11:31 2020

@author: luke
"""

import pandas as pd
import json
from numpy import any as npany
from numpy import isin
from itertools import product
from collections import Counter
from random import choice
from os.path import join
from pulp import makeDict,LpProblem,LpVariable,LpMinimize,LpInteger, LpContinuous, LpBinary
pd.set_option('display.max_columns', 10)

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

    @staticmethod
    def get_meal_counts(day):
        return [meal['mealType'] for meal in day['mealTypes']]

    @staticmethod
    def get_cooking_limit_counts(day):
        return [{meal['mealType']:meal['cookingTimeLimit']} for meal in day['mealTypes']]
    
    def get_number_of_mealtimes(self,details):
        counts = dict(Counter([item for sublist in map(lambda day: self.get_meal_counts(day), 
                                                details['dayOptions']) for item in sublist]))
        return counts

    @staticmethod
    def get_people_servings(details):
        return details['numberOfPeople']  
    
    @staticmethod
    def get_diet_type(details):
        return details['dietType']    

    @staticmethod
    def get_plan_duration(details):
        return details['planDuration']   
    
    @staticmethod    
    def get_day_options(details):
        return details['dayOptions']           
        
    def get_cooking_time_limits(self,details):
        look=[item for sublist in map(lambda day: self.get_cooking_limit_counts(day), 
                                                    details['dayOptions']) for item in sublist]
        dinner=max(list(map(lambda x:x['dinner'] if 'dinner' in x else -1,look)))
        lunch=max(list(map(lambda x:x['lunch'] if 'lunch' in x else -1,look)))
        if lunch == -1 and dinner !=-1:
            return {'dinner' : dinner}
        elif lunch != -1 and dinner ==-1:
            return {'lunch' : lunch}
        elif lunch == -1 and dinner ==-1:
            return {}
        else:
            return {'lunch' : lunch, 'dinner' : dinner} 

    
        
class load_files(options):
    def __init__(self,splitmealtimes = True, details = None, **kwargs):
        fvars = {'recipepath' : './recipes/',
                 'recipelookuppath' : '.',
                 'recipelookupname' : 'recipelookup',
                 'ingredientspath' : './ingredients/',
                 'ingredientsname' : 'ingredients'
                 }
        fvars.update(**kwargs)
        options.__init__(self,splitmealtimes=splitmealtimes, **kwargs)
        self.splitmealtimes=splitmealtimes
        self.recipelookupname = join(fvars['recipelookuppath'],fvars['recipelookupname'])
        self.ingredientsname = join(fvars['ingredientspath'],fvars['ingredientsname'])
        self.rdir = fvars['recipepath']
        self.idir = fvars['ingredientspath']
        if details is None:
            self.people_servings = None
            self.diet_type = None
            self.plan_duration = None
            self.time_limits = None
            self.meal_times = None
            self.nooflunch = None
            self.noofdinner = None
            self.day_options = None
        else:
            self.get_meal_plan_options(details)
    
    @staticmethod
    def recipe_file_mapping(nam,rdir):
        with open(rdir+nam+'.json') as file:
            rec = json.load(file)
        return rec
    
    def load_ingredients(self):
        path = '{}.json'.format(self.ingredientsname)
        with open(path) as file:
            ing = json.load(file)
        self.ingredients = pd.DataFrame(ing['items']).set_index('name')
        
    @staticmethod
    def mealtimeapply(x,mealtime='lunch'):
        if npany(pd.isnull(x.mealTime)):
            out=0
        else:
            if mealtime in x.mealTime:
                out = 1
            else:
                out = 0
        return out

    @staticmethod
    def update_quant(x,alter = 0.25):
        quant = x['quant']
        quant *= alter
        x['quant'] = quant
        return x
    
    def adjust_ingredients(self,x,serves, meal_plan_servings):
        if x == [0]:
            return [0]
        else:
            alter = meal_plan_servings/serves
            return list(map(lambda x: self.update_quant(x, alter=alter),x))
        
    def load_recipes(self):
        names = pd.read_csv('{}.csv'.format(self.recipelookupname))
        recs = pd.DataFrame(list(map(lambda name: self.recipe_file_mapping(name,self.rdir), names.Name))).set_index('name')
        if self.people_servings is not None:
            list(map(lambda x,y: self.adjust_ingredients(x,y,self.people_servings),recs.ingredients,recs.serves))
        dump = pd.DataFrame([[0,[0]]],columns = ['ingno','ingredients'],index=['dump'])
        recs['Lunch']=recs.apply(lambda x: self.mealtimeapply(x), axis=1)
        recs['Dinner']=recs.apply(lambda x: self.mealtimeapply(x,mealtime='dinner'), axis=1)
        if self.splitmealtimes:       
            ents = recs.loc[(recs.Lunch == 1)&(recs.Dinner == 1)].copy()
            ents.mealTime = 'Dinner'
            ents.index += '_dinner'
            ents.Lunch = 0
            recs.loc[(recs.Lunch == 1)&(recs.Dinner == 1),'Dinner'] = 0
            recs = recs.append(ents)
        else:
            recs.loc[(recs.Lunch == 1)&(recs.Dinner == 1),'Lunch'] = 0
        self.recipes = recs.append(dump)
        if self.time_limits is not None:
            dropinds = []
            if 'lunch' in self.time_limits:
                time = self.time_limits['lunch']
                dropinds += list(self.recipes.loc[(self.recipes.Lunch == 1)&(self.recipes.cookingTime > time)].index)       
            if 'dinner' in self.time_limits:
                time = self.time_limits['dinner']
                dropinds += list(self.recipes.loc[(self.recipes.Dinner == 1)&(self.recipes.cookingTime > time)].index)  
            self.recipes.drop(dropinds,inplace=True)
        if self.diet_type is not None:
           self.recipes=self.recipes.loc[(self.recipes.type==self.diet_type)|pd.isnull(self.recipes.type)]
         
            
    def get_meal_plan_options(self,details):
        self.people_servings = self.get_people_servings(details)
        self.diet_type = self.get_diet_type(details)
        self.plan_duration = self.get_plan_duration(details)
        self.time_limits = self.get_cooking_time_limits(details)
        self.meal_times = self.get_number_of_mealtimes(details)
        if 'lunch' in self.meal_times.keys():
            self.nooflunch = self.meal_times['lunch']
        else:
            self.nooflunch = 0
        if 'dinner' in self.meal_times.keys():
            self.noofdinner = self.meal_times['dinner']    
        else:
            self.noofdinner = 0
        self.day_options = self.get_day_options(details)    
        
        
class optimisation(load_files):
    def __init__(self,ln=1E7,noofdays=1, nooflunch=1, noofdinner=1, splitmealtimes=True, 
                 solvername='ScranPlanSoln', details = None,**kwargs):
        load_files.__init__(self,splitmealtimes=splitmealtimes, details = details, **kwargs)
        self.ln=ln
        self.cost=None
        self.solvername=solvername
        self.noofdays=noofdays
        if self.nooflunch is None:
            self.nooflunch=nooflunch
        if self.noofdinner is None:
            self.noofdinner=noofdinner
        self.load_ingredients()
        self.load_recipes()
        self.make_grid()
        self.create_cost_matrix()
        self.setup_supply_and_demand()
        self.setup_solver_env()
        self.setup_constraints()
    
    @staticmethod
    def inner_dict(x,y):
        return dict(map(lambda y: (y,'route__{}_{}'.format(x,y)),y))
    
    @staticmethod
    def get_value(x,p):
        return p[x].varValue
    
    def create_soln_grid(self,sup,dem):
        self.soln=pd.DataFrame(dict(map(lambda x: (x,self.inner_dict(x,dem)),sup))).T
    
    def setup_supply_and_demand(self):
        rlen=len(self.recipes)
        rvals=[1]*rlen
        self.dem = pd.DataFrame(rvals,index=self.recipes.index,columns=['values'])
        supply = self.ingredients.to_dict()['cost']
        demand = self.dem.to_dict()['values']        
        self.supl = list(supply)
        self.deml = list(demand)
        self.create_soln_grid(self.supl, self.deml)
    
    def make_grid(self):
        self.grid = list(product(self.ingredients.index,self.recipes.index))
        
    def create_cost_matrix(self):
        self.costmat=pd.DataFrame([],columns=self.recipes.index,index=self.ingredients.index)
        self.costmat.fillna(self.ln,inplace=True)
        self.ingredients['costperquant'] = self.ingredients.cost/self.ingredients.quant
        self.costmat.apply(lambda x: self.fill_costmat(x.name))
        
    def fill_costmat(self,col):
        if col !='dump':
            rec=self.recipes[col:col]
            includedings = pd.DataFrame(rec.ingredients[0]).name
            lookup=self.ingredients.loc[isin(self.ingredients.parentName,includedings)].index
            self.costmat.loc[self.costmat[col].index.isin(lookup),col] = self.ingredients.costperquant[lookup]
        else:
            self.costmat[col]=self.ingredients.costperquant
    
    def setup_solver_env(self):
        costsl=self.costmat.values.tolist()
        costs=makeDict([self.supl,self.deml], costsl,0)
        
        self.x = LpVariable.dicts("route_", (self.supl, self.deml), 
                            lowBound = 0, 
                            cat = LpContinuous)
        
        self.xb = LpVariable.dicts("choice_", (self.deml), 
                            lowBound = 0, 
                            upBound =1,
                            cat = LpBinary)
        
        self.xi = LpVariable.dicts("items_", (self.supl,self.deml), 
                            lowBound = 0, 
                            upBound =1,
                            cat = LpInteger)
        
        self.prob = LpProblem(self.solvername, LpMinimize)
        
        objfunc=[]  
        objfunc+=[self.x[w][b]*costs[w][b] for (w,b) in self.grid]
        
        self.prob += sum(objfunc), \
                    "Sum_of_Recipe_Costs"
                    
    def setup_constraints(self):
        #Constraints
        
        #t1=[]
        #for b in self.dem.index[:-1]:
         #   t1+=[self.xb[b]]  
        #self.prob += sum(t1) ==self.noofdays, \
        #"Number_of_meals_constrtaints_%s"       

        for b in self.dem.index[:-1]:
            for it in self.recipes[b:b].ingredients[0]:
                w=it['name']
                ingsadd=self.ingredients.loc[self.ingredients.parentName==w]
                add=[-self.x[i][b] for i in ingsadd.index]
                self.prob +=add+it['quant']*self.xb[b]<=0, \
            "Quantity_of_ingredients_constrtaints_%s"%b+w
            
        for b in self.dem.index[:-1]:
            for it in self.recipes[b:b].ingredients[0]:
                w=it['name']
                self.prob +=self.x[w][b]-it['quant']*self.xb[b]<=0, \
            "dump_constrtaints_%s"%b+w
            
        for b in self.dem.index[:-1]:
            t1=[]
            for w in self.ingredients.index:
                t1+=[self.x[w][b]]  
            self.prob +=-sum(t1)+self.xb[b]<=0, \
            "force_meals_constrtaints_%s"%b 
        
        for w in self.ingredients.index:
            t1=[]
            for b in self.dem.index:
                quant=self.ingredients[w:w].quant.values[0]
                t1+=[self.x[w][b]*1./quant-self.xi[w][b]]
            self.prob += sum(t1)==0, \
            "whole_products_constrtaints_%s"%w 
            
        t1=[]
        for b in self.recipes.loc[self.recipes['Lunch']==1].index:
            t1+=[self.xb[b]]
        self.prob += sum(t1) ==self.nooflunch, \
        "Number_of_lunchs_constrtaints_%s"       
        
        t1=[]
        for b in self.recipes.loc[self.recipes['Dinner']==1].index:
            t1+=[self.xb[b]]
        self.prob += sum(t1) ==self.noofdinner, \
        "Number_of_dinners_constrtaints_%s"       

    def solve(self):
        check=self.prob.solve()
        if check>0:
            out={'status': True}
            self.cost=round(self.prob.objective.value(),2)
        else:
            out={'status': False}  
        return out
    
    def get_solution(self,refine=True):
        soln = self.soln.applymap(lambda x: self.get_value(x,self.prob.variablesDict()))
        if refine:
            soln = soln.loc[((soln.T != 0).any())]
            soln = soln.loc[:, (soln!=0).any(axis=0)]
        self.format_dayoptions(soln)
        self.format_remaining_food(soln)
        out = {'dietType': self.diet_type, 
               'estimatedCost': self.cost, 
               'details': self.day_options, 
               'remainingFood' : self.remainder}        
        return out

    @staticmethod
    def make_ingredients_out(x,ingredients):
        name=x[0]
        quant=x[1]
        unit=ingredients.loc[name,'unit']
        return {'name': name, 'quantity': quant, 'unit': unit}

    def format_remaining_food(self,solution):
        remainder = solution['dump'].loc[solution['dump']>0].to_dict()
        self.remainder = list(map(lambda x: self.make_ingredients_out(x,self.ingredients),remainder.items()))
        
    def format_dayoptions_iter(self,day,lunches,dinners):
        for meal in day['mealTypes']:
            meal.pop('cookingTimeLimit')
            if meal['mealType'] == 'lunch':
                name = choice(lunches.columns)
                ct = self.recipes.loc[name,'cookingTime']
                meal['name'] = name
                meal['cookingTime'] = ct
                ingredients = lunches[name].loc[lunches[name]>0].to_dict()
                meal['ingredients'] = list(map(lambda x:  \
                                               self.make_ingredients_out(x,self.ingredients),
                                               ingredients.items()))         
                lunches.drop(name,axis=1,inplace=True)
            if meal['mealType'] == 'dinner':
                name = choice(dinners.columns)
                ct = self.recipes.loc[name,'cookingTime']
                if len(name.split('_'))>1:
                    while any([True for meal in day['mealTypes'] if 'name' in  \
                               meal and meal['name']==name.split('_')[0]]):
                        name = choice(dinners.columns)
                meal['name'] = name.split('_')[0] 
                meal['cookingTime'] = ct
                ingredients = dinners[name].loc[dinners[name]>0].to_dict()
                meal['ingredients'] = list(map(lambda x: \
                                               self.make_ingredients_out(x,self.ingredients),
                                               ingredients.items()))                  
                dinners.drop(name,axis = 1,inplace=True)
            
    def format_dayoptions(self,solution):
        lcheck = list(self.recipes.loc[self.recipes.Lunch == 1].index)
        if any([True for i in lcheck if i in solution.columns]):
            lunches = solution[self.recipes.loc[self.recipes.Lunch == 1].index].copy()
        
        dcheck = list(self.recipes.loc[self.recipes.Dinner == 1].index)
        if any([True for i in dcheck if i in solution.columns]):
            dinners = solution[self.recipes.loc[self.recipes.Dinner == 1].index].copy()
        
        list(map(lambda x: self.format_dayoptions_iter(x,lunches,dinners),self.day_options))