from time import clock
from copy import *
global PROFILE_FUNCTIONS
PROFILE_FUNCTIONS = True
global PROFILE_RESULTS
PROFILE_RESULTS = {}

def profile (func):
    if(PROFILE_FUNCTIONS == True):
        def function_wrapper(*args, **kwargs):
            start = clock()
            func(*args, **kwargs)
            duration = clock() - start
            curr_func_name = func.__name__
            print len(PROFILE_RESULTS)
            if len(PROFILE_RESULTS) != 0:
                for name, value in PROFILE_RESULTS.copy().iteritems():
                    if(curr_func_name == name):
                        old_count = deepcopy(value[1])
                        old_avg = deepcopy(value[0])
                        new_count = value[1] + 1
                        new_avg = (old_avg*old_count + duration)/new_count
                        value = (new_avg, new_count)
                    else: 
                        PROFILE_RESULTS[curr_func_name] = (duration, 1)
            else:
                PROFILE_RESULTS[curr_func_name] = (duration, 1)
        return function_wrapper
    else:
        return func
    
#test function for q1
@profile
def countdown(num):
    if num == 1:
        print num
        return
    else: 
        print num
        return countdown(num-1)    
        

