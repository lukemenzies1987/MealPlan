#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 15:58:47 2020

@author: luke
"""

from OptimisationLibrary import optimisation

opt=optimisation(noofdays=4)
check=opt.solve()
print ("Total Cost of Meal Plan = £{:.2f}".format(opt.cost))
soln=opt.get_solution()
soln=soln.loc[((soln.T != 0).any())]
soln=soln.loc[:, (soln!=0).any(axis=0)]