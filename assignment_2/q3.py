def my_map(function, iterator): 
    return_list = []
    for x in iterator:
        result = function(x)
        return_list.append(result)
    return return_list

def my_filter(function, iterator): 
    return_list = []
    print function
    for x in iterator:
        if(function(x)) == True:
            return_list.append(x)
    return return_list

def my_reduce(function, iterator):
    result = None;
    for x in iterator:
        if(x == 0):
            result = x
        else:
            result = function(result, x)
    return result
        
#if __name__ == "__main__":
    #print "in main"    
    #l = [1,2,3,4]
    #largest = my_map(lambda x: x**2, l)
    #y = [-2,-1,0,1,2]
    #non_negative = my_filter(lambda x: x>0, y)
    #summation = my_reduce(lambda x, z: x+z, l)
    #print largest
    #print non_negative
    #print summation


