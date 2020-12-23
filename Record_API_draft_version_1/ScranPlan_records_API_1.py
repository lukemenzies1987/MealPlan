#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Dec 22 11:31:11 2020

This is the API used for creating, deleting and modifying records for ScranPlan.

@author: luke
"""
import flask
from flask import request
import sys
import json
#sys.path.append('..') #Add if needed to specify path of main library.
from Database_API_Library import database
app = flask.Flask(__name__)
app.config["DEBUG"] = True

db=database(path='.')


@app.route('/api/v1/createaccount', methods=['POST'])
def api_create_account():
    db.load(db.filename)
    body = json.loads(request.data)
    if 'username' in body:
        user=body['username']
    else:
        return {'status': 'No username given'}
    out=db.add_user(user)
    db.save(db.filename)
    return out

@app.route('/api/v1/findaccount', methods=['POST'])
def api_find_account():
    db.load(db.filename)
    body = json.loads(request.data)
    if 'username' in body:
        user=body['username']
    else:
        return {'status': 'No username given'}
    key = (user, 'USER')
    try:
        check=db.database.loc[key]
        out={'status': 'User found',
             'username': user,
             'dateCreated' : check.timestamp
             }
    except KeyError:
        out={'status': 'User does not exist'}
    return out

@app.route('/api/v1/findmealplan', methods=['POST'])
def api_find_mealplan():
    db.load(db.filename)
    body = json.loads(request.data)
    if 'username' in body:
        user=body['username']
    else:
        return {'status': 'No username given'}   
    key = (user, 'USER')
    status=db.check_exists(key)
    if status==False:
        return {'status': 'User does not exist'}   
    if 'mealPlanName' in body:
        meal_plan_name=body['mealPlanName']
    else:
        return {'status': 'No meal plan name given'} 
    details=db.get_mealplan_details(user, meal_plan_name)
    if details['status']:
        out={'status': 'Meal plan found',
            'username': user,
            'mealPlanName' : meal_plan_name,
            'details' : details['details']
            }
    else:
        out=details
    return out

@app.route('/api/v1/createmealplan', methods=['POST'])
def api_create_mealplan():
    db.load(db.filename)
    body = json.loads(request.data)
    if 'username' in body:
        user=body['username']
    else:
        return {'status': 'No username given'}   
    key = (user, 'USER')
    status=db.check_exists(key)
    if status==False:
        return {'status': 'User does not exist'}   
    if 'mealPlanName' in body:
        meal_plan_name=body['mealPlanName']
    else:
        return {'status': 'No meal plan name given'}  
    if 'details' in body:
        details=body['details']
    else:
        return {'status': 'No details given'}  
    key = ('{}#{}'.format(meal_plan_name,user),'MEALPLAN')
    try:
        check=db.database.loc[key]
        out={'status': 'Meal plan already exists',
             'username': user,
             'mealPlanName' : meal_plan_name,
             'dateCreated' : check.timestamp
             }
    except KeyError:
        status=db.add_mealplan(user, meal_plan_name, details)
        if status['status']:
            out={'status': 'Meal plan created',
                 'username': user,
                 'mealPlanName' : meal_plan_name
                 }      
            #db.save(db.filename)
        else:
            out=status
    return out

@app.route('/api/v1/updatemealplan', methods=['POST'])
def api_update_mealplan():
    db.load(db.filename)
    body = json.loads(request.data)
    if 'username' in body:
        user=body['username']
    else:
        return {'status': 'No username given'}   
    key = (user, 'USER')
    status=db.check_exists(key)
    if status==False:
        return {'status': 'User does not exist'}   
    if 'mealPlanName' in body:
        meal_plan_name=body['mealPlanName']
    else:
        return {'status': 'No meal plan name given'}  
    if 'details' in body:
        details=body['details']
    else:
        return {'status': 'No details given'}  
    status=db.update_mealplan(user,meal_plan_name,details)
    if status['status']:
        db.save(db.filename)
    return status

@app.route('/api/v1/deletemealplan', methods=['POST'])
def api_delete_mealplan():
    db.load(db.filename)
    body = json.loads(request.data)
    if 'username' in body:
        user=body['username']
    else:
        return {'status': 'No username given'}   
    key = (user, 'USER')
    status=db.check_exists(key)
    if status==False:
        return {'status': 'User does not exist'}   
    if 'mealPlanName' in body:
        meal_plan_name=body['mealPlanName']
    else:
        return {'status': 'No meal plan name given'}  
    status=db.delete_mealplan(user,meal_plan_name)
    db.save(db.filename)
    return status

app.run()