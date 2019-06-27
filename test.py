def makeBoolean(list):
    result = "("
    for i in range(0,len(list)-1):
        result+= list[i]+"=1 or "
    result += list[len(list)-1]+" = 1 ) "
    return result
