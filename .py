def recursive(n):
    if n == 1:
        return 1
    return n * recursive(n - 1)

ww = recursive(5)
print(ww)

def recursive(n):
    if n == 0:
        return 0
    
    if n == 1:
        return 1
    return recursive(n - 1)  + recursive(n - 2)

ww = recursive(-1)
print(ww)

