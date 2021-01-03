#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 29 15:58:47 2020

@author: luke
"""

from OptimisationLibrary import optimisation

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
                                    {'mealType': 'lunch', 'cookingTimeLimit': 30
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

opt=optimisation(details=mealplandetails['details'])
check=opt.solve()
if check['status']==False:
    print('Didn\'t optimise')
else:
    print ("Total Cost of Meal Plan = £{:.2f}".format(opt.cost))
soln=opt.get_solution()