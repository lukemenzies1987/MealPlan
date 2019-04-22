#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 25 17:56:29 2018

@author: luke
"""

import pandas as pd
import json
from os import remove
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

ings=pd.DataFrame(ing['items'])
ings.index=ings.name
del ings['name']


noofdays=2

days=['Day_'+str(d+1) for d in range(noofdays)]
dvals=[0]*noofdays
#dem=pd.DataFrame(dvals,index=days,columns=['values'])
dump=pd.DataFrame([[0,[0]]],columns=['ingno','ingredients'],index=['dump'])
recipes=pd.DataFrame(recs)
recipes.index=recipes.Name
recipes=recipes.append(dump)
del recipes['Name']
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
        costmat.loc[costmat[col].index.isin(includedings),col]=ings.costperquant[includedings]
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
prob += sum(t1) ==noofdays, \
"Number_of_meals_constrtaints_%s"       
#for b in dem.index:
 #   prob += xb[b] <=1
for b in dem.index[:-1]:
    
    for it in recipes[b:b].ingredients[0]:
        w=it['name']
        prob +=-x[w][b]+it['quant']*xb[b]<=0, \
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
        
dfr=dfr.T
"""
for i in dem:
    df1=df1.apply(lambda x: 0 if not is_numlike(x[i]) else x[i],axis=1)
            
df1=df1.loc[:, (df1 != 0).any(axis=0)]
   
df.append(df1)
"""