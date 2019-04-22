#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Apr 22 14:04:10 2019

@author: luke
"""

from git import Repo
import os
import sys

cwd=os.getcwd()
PATH_OF_GIT_REPO = os.path.join(cwd,'.git')  # make sure .git folder is properly configured
COMMIT_MESSAGE = sys.argv[1]#'comment from python script'
print(PATH_OF_GIT_REPO)
print(COMMIT_MESSAGE)
def git_push():
    try:
        repo = Repo(PATH_OF_GIT_REPO)
        repo.git.add(update=True)
        repo.index.commit(COMMIT_MESSAGE)
        origin = repo.remote(name='origin')
        origin.push('origin','https://github.com/lukemenzies1987/MealPlan.git')
    except:
        print('Some error occured while pushing the code')
    finally:
        print('Code push from script succeeded')       

git_push()