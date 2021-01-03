#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 25 17:56:29 2018

@author: luke
"""

import pandas as pd
import json
from os import remove
import numpy as np
from pulp import makeDict,LpProblem,LpVariable,LpMinimize,LpInteger, LpContinuous, LpBinary
pd.set_option('display.max_columns', 10)

ln=1E7
name='recipelookup'
rdir='./recipes/'
recl=pd.read_csv(name+'.csv')
recs=[]
for nam in recl.Name:
    with open(rdir+nam+'.json') as file:
        rec=json.load(file)
    file.close()
    recs.append(rec)

def search(values, searchFor):
    for k in values:
        for v in values[k]:
            if searchFor in v:
                return k
    return None

idir='./ingredients/'
name='ingredients'
with open(idir+name+'.json') as file:
    ing=json.load(file)
file.close()

ings=pd.DataFrame(ing['items'])#.set_index('name')
ings.index=ings.name
del ings['name']


noofdays=2
nooflunch=1
noofdinner=3

mealplandetails={'status': True,
                 'message': 'Found meal plan',
                 'details': {'type': 'personal',
                  'numberOfPeople': 1.0,
                  'dietType': 'regular',
                  'portionSizes': 'medium',
                  'planDuration': 'weekly',
                  'freezeIngredients': True,
                  'ingredientFlexibility': False,
                  'otherOptions': [],
                  'dietaryRequirement': [],
                  'dayOptions': [
                            {'day': 1,
                                    'mealTypes': [
                                    {'mealType': 'lunch', 'cookingTimeLimit': 60
                                    },
                                    {'mealType': 'dinner', 'cookingTimeLimit': 60
                                    }
                                ]
                            },
                            {'day': 2,
                                'mealTypes': [
                                    {'mealType': 'dinner', 'cookingTimeLimit': 60
                                    }
                                ]
                            },
                            {'day': 3,
                                'mealTypes': [
                                    {'mealType': 'dinner', 'cookingTimeLimit': 60
                                    }
                                ]
                            }
                        ]
                    }
                }



def mealtimeapply(x,mealtime='lunch'):
    if np.any(pd.isnull(x.mealTime)):
        out=0
    else:
        if mealtime in x.mealTime:
            out=1
        else:
            out=0
    return out

def update_quant(x,alter=0.25):
    quant=x['quant']
    quant*=alter
    x['quant']=quant
    return x

def adjust_ingredients(x,serves,meal_plan_servings):
    if x == [0]:
        return [0]
    else:
        alter=meal_plan_servings/serves
        return list(map(lambda x: update_quant(x,alter=alter),x))
    
days=['Day_'+str(d+1) for d in range(noofdays)]
dvals=[0]*noofdays
#dem=pd.DataFrame(dvals,index=days,columns=['values'])
dump=pd.DataFrame([[0,[0]]],columns=['ingno','ingredients'],index=['dump'])
recipes=pd.DataFrame(recs)
servings=mealplandetails['details']['numberOfPeople']
list(map(lambda x,y: adjust_ingredients(x,y,servings),recipes.ingredients,recipes.serves))
recipes.index=recipes['name']
recipes['Lunch']=recipes.apply(lambda x: mealtimeapply(x), axis=1)
recipes['Dinner']=recipes.apply(lambda x: mealtimeapply(x,mealtime='dinner'), axis=1)

ents=recipes.loc[(recipes.Lunch==1)&(recipes.Dinner==1)].copy()
ents.mealTime='Dinner'
ents.index+='_dinner'
ents.Lunch=0
recipes.loc[(recipes.Lunch==1)&(recipes.Dinner==1),'Dinner']=0
recipes=recipes.append(ents)
recipes=recipes.append(dump)
del recipes['name']
rlen=len(recipes)
rvals=[1]*rlen



dem=pd.DataFrame(rvals,index=recipes.index,columns=['values'])

supply=ings.to_dict()['cost']

demand=dem.to_dict()['values']

supl=list(supply)
deml=list(demand)

grid=[]
for i in ings.index:
    for r in recipes.index:
        grid.append((i,r))

costmat=pd.DataFrame([],columns=recipes.index,index=ings.index)
costmat.fillna(ln,inplace=True)
ings['costperquant']=ings.cost/ings.quant

for col in costmat.columns:
    if col !='dump':
        rec=recipes[col:col]
        includedings=pd.DataFrame(rec.ingredients[0]).name
        lookup=ings.loc[np.isin(ings.parentName,includedings)].index
        costmat.loc[costmat[col].index.isin(lookup),col]=ings.costperquant[lookup]
    else:
        costmat[col]=ings.costperquant
    
costsl=costmat.values.tolist()
costs=makeDict([supl,deml], costsl,0)

x = LpVariable.dicts("route_", (supl, deml), 
                    lowBound = 0, 
                    cat = LpContinuous)

xb = LpVariable.dicts("choice_", (deml), 
                    lowBound = 0, 
                    upBound =1,
                    cat = LpBinary)

xi = LpVariable.dicts("items_", (supl,deml), 
                    lowBound = 0, 
                    upBound =1,
                    cat = LpInteger)

prob = LpProblem("Testing", LpMinimize)


objfunc=[]  
objfunc+=[x[w][b]*costs[w][b] for (w,b) in grid]

# The objective function is added to 'prob' first
prob += sum(objfunc), \
            "Sum_of_Transporting_Costs"
            
#Constraints
t1=[]
for b in dem.index[:-1]:
    t1+=[xb[b]]  
#prob += sum(t1) ==noofdays, \
#"Number_of_meals_constrtaints_%s"       
#for b in dem.index:
 #   prob += xb[b] <=1

for b in dem.index[:-1]:
    for it in recipes[b:b].ingredients[0]:
        w=it['name']
        ingsadd=ings.loc[ings.parentName==w]
        #split=1/len(ingsadd)
        #for i in ingsadd.index:
        add=[-x[i][b] for i in ingsadd.index]
        prob +=add+it['quant']*xb[b]<=0, \
    "Quantity_of_ingredients_constrtaints_%s"%b+w
    
for b in dem.index[:-1]:
    for it in recipes[b:b].ingredients[0]:
        w=it['name']
        prob +=x[w][b]-it['quant']*xb[b]<=0, \
    "dump_constrtaints_%s"%b+w
    

for b in dem.index[:-1]:
    t1=[]
    for w in ings.index:
        t1+=[x[w][b]]  
    prob +=-sum(t1)+xb[b]<=0, \
    "force_meals_constrtaints_%s"%b 

for w in ings.index:
    t1=[]
    for b in dem.index:
        quant=ings[w:w].quant.values[0]
        t1+=[x[w][b]*1./quant-xi[w][b]]
    prob += sum(t1)==0, \
    "whole_products_constrtaints_%s"%w 

t1=[]
for b in recipes.loc[recipes['Lunch']==1].index:
    t1+=[xb[b]]
prob += sum(t1) ==nooflunch, \
"Number_of_lunchs_constrtaints_%s"       

t1=[]
for b in recipes.loc[recipes['Dinner']==1].index:
    t1+=[xb[b]]
prob += sum(t1) ==noofdinner, \
"Number_of_dinners_constrtaints_%s"       

prob.writeLP('test')              
prob.solve()
cost=round(prob.objective.value(),2)
print ("Total Cost of Transportation = £{:.2f}".format(cost))
print(prob.status)
soln=[]
for v in prob.variables():
    soln.append([v.name,v.varValue])

pd.DataFrame(x).to_csv('df.csv')
dfr=pd.read_csv('df.csv',index_col=0)
remove(r'./df.csv')
for i in dfr.columns:
    for c,d in soln:
        try:
            if len(dfr.loc[dfr[i]==c,i])!=0:
                #print(dfr.loc[dfr[i]==c,i],c)
                dfr.loc[dfr[i]==c,i]=d
        except TypeError:
            continue#print(dfr.loc[dfr[i]==c],i)
        
dfr=dfr.T.infer_objects()

out={}

