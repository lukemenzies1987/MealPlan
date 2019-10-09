#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 27 13:39:39 2019

@author: luke
"""

import pandas as pd
import json
from os import remove
import os
import numpy as np
from pulp import makeDict,LpProblem,LpVariable,LpMinimize,LpInteger, LpContinuous, LpBinary
pd.set_option('display.max_columns', 10)


def search(values, searchFor):
    for k in values:
        for v in values[k]:
            if searchFor in v:
                return k
    return None

ddir='./directions/'

mealrecs={"Noodays": 3,
          "recipes":["chilliconcarne", "fajitaschicken", "pastabake"]        
        }

for r, d, f in os.walk(ddir):
    files=f
    
check=[rec for rec in files if rec.replace('.json','') in mealrecs['recipes']]
adirs=[]
for r in check:
    with open(ddir+r) as file:
        dirs=json.load(file)
        adirs.append(dirs)
file.close()

steptypes=['collecting','cutting','washing']
        
noofdays=mealrecs['Noodays']


daydim=['day_'+str(i+1) for i in range(noofdays)]  
x = LpVariable.dicts("route_", (steptypes,daydim, mealrecs['recipes']), 
                    lowBound = 0, 
                    cat = LpContinuous)

grid=[]
reduction=dict([])
block=dict([])
for s in steptypes:
    reduction[s]=30
    for d in daydim:
        block[d]=1
        for r in mealrecs['recipes']:
            grid.append((s,d,r))


block=dict([])
for cnts,s in enumerate(steptypes):
    block[s]=dict([])
    for cntd,d in enumerate(daydim):
        block[s][d]=dict([])  
        for cntr,r in enumerate(mealrecs['recipes']):
            block[s][d][r]=1
            if cntd==cntr:
                block[s][d][r]=0
                
arrays = [steptypes,daydim]
ind=pd.MultiIndex.from_product(arrays)

costmat=pd.DataFrame([],columns=ind,index=mealrecs['recipes'])

for a in adirs:
    steps=a['steps']
    for stp in steps:
        costmat[stp['type']].loc[a['Name']]=stp['time']
 
costl = np.zeros((noofdays,len(mealrecs['recipes']),len(steptypes)))    
for cnt,s in enumerate(steptypes):
    costl[cnt]=costmat[s].values
    
costs=makeDict([steptypes,daydim, mealrecs['recipes']], costl,0)

objfunc=[]  
#objfunc+=[x[s][d][r]*costs[s][d][r] for (s,d,r) in grid]

for d in daydim:
    #block.update(dict.fromkeys(daydim, 1))
    #block[d]=1
    for s in steptypes:
        objfunc+=[x[s][d][r]*costs[s][d][r]-reduction[s]*block[s][d][r]*x[s][d][r] for r in mealrecs['recipes']]