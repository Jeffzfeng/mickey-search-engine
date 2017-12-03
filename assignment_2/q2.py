def find_product(l):    
    viable_ranges = filter(lambda x: x+5<=len(l), range(len(l)))   
    products = (map(lambda u: reduce(lambda z,q: z*q, map(lambda y: l[y+u], range(5))), viable_ranges))
    largest_index = filter(lambda x: len(filter(lambda y: products[y] < products[x], range(len(products)))) == (len(products)-1), range(len(products)))
    largest = map(lambda x: products[x], largest_index)
    return largest_index.pop(0), largest.pop(0)
    
#if __name__ == "__main__":
    #print "in main"
    #product = find_product([3,4,5,6,4])
    #test = find_product([1,2,3,4,5,6,4,2,1,3])
    #print test
