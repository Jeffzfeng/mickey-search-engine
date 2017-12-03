import re

def split_sentence(filename):
    with open(filename) as file:
        result = ''        
        for i in file:
            result = result + i
        concatenated = result.replace('\n', ' ').replace('\r', '') 
        split_lines = re.split('(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?|\!)\s', concatenated)
        file.close()
    
    with open('q5.out', 'w') as output:
        type(split_lines)
        #output.write('hiiii')
        #output.close()
        for i in split_lines:
            if(i == split_lines[len(split_lines)-1]):
                break
            else:
                output.write(i)
                output.write('\n')
        output.close()
       
#if __name__ == "__main__":
    #split_sentence('cool')
