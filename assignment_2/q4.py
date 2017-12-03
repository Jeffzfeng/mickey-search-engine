def find_popular(filename):
    popular_words_dict = {}
    popular_words_list = []
    popularity_list_word_only = []
    try :
        with open(filename) as file:
            for line in file:
                for word in line.split():
                    if word not in popular_words_dict:
                        popular_words_dict[word] = 1
                    else:
                        popular_words_dict[word] += 1   
                    
        for key in popular_words_dict:
            word_popularity = key, popular_words_dict[key]
            popular_words_list.append(word_popularity)
        
        popular_words_list.sort(key = lambda x: x[1], reverse = True)
        for i in popular_words_list:
            popularity_list_word_only.append(i[0])
        
        final_word_list = popularity_list_word_only[:10]
        return final_word_list

    except :
        print 'Something went wrong'
