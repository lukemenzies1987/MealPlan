#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 11:11:31 2020

@author: luke
"""

import pandas as pd
import json
from itertools import product
from os.path import join
from pulp import makeDict,LpProblem,LpVariable,LpMinimize,LpInteger, LpContinuous, LpBinary
pd.set_option('display.max_columns', 10)


class load_files():
    def __init__(self,**kwargs):
        fvars = {'recipepath' : './recipes/',
                 'recipelookuppath' : '.',
                 'recipelookupname' : 'recipelookup',
                 'ingredientspath' : './ingredients/',
                 'ingredientsname' : 'ingredients'
                 }
        fvars.update(**kwargs)
        self.recipelookupname = join(fvars['recipelookuppath'],fvars['recipelookupname'])
        self.ingredientsname = join(fvars['ingredientspath'],fvars['ingredientsname'])
        self.rdir = fvars['recipepath']
        self.idir = fvars['ingredientspath']
    
    @staticmethod
    def recipe_file_mapping(nam,rdir):
        with open(rdir+nam+'.json') as file:
            rec=json.load(file)
        return rec
    
    def load_ingredients(self):
        path='{}.json'.format(self.ingredientsname)
        with open(path) as file:
            ing=json.load(file)
        self.ingredients = pd.DataFrame(ing['items']).set_index('name')
    
    def load_recipes(self):
        names = pd.read_csv('{}.csv'.format(self.recipelookupname))
        recs = list(map(lambda name: self.recipe_file_mapping(name,self.rdir), names.Name))
        dump = pd.DataFrame([[0,[0]]],columns = ['ingno','ingredients'],index=['dump'])
        self.recipes = pd.DataFrame(recs).set_index('name').append(dump)
    
class optimisation(load_files):
    def __init__(self,ln=1E7,noofdays=1,solvername='ScranPlanSoln',**kwargs):
        load_files.__init__(self, **kwargs)
        self.ln=ln
        self.solvername=solvername
        self.noofdays=noofdays
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
            self.costmat.loc[self.costmat[col].index.isin(includedings),col] = self.ingredients.costperquant[includedings]
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
        t1=[]
        for b in self.dem.index[:-1]:
            t1+=[self.xb[b]]  
        self.prob += sum(t1) ==self.noofdays, \
        "Number_of_meals_constrtaints_%s"       
        #for b in dem.index:
         #   prob += xb[b] <=1
        for b in self.dem.index[:-1]:
            for it in self.recipes[b:b].ingredients[0]:
                w=it['name']
                self.prob +=-self.x[w][b]+it['quant']*self.xb[b]<=0, \
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

    def solve(self):
        check=self.prob.solve()
        if check>0:
            out={'status': True}
            self.cost=round(self.prob.objective.value(),2)
        else:
            out={'status': False}  
        return out
    
    def get_solution(self):
        out=self.soln.applymap(lambda x: self.get_value(x,self.prob.variablesDict()))
        return out