from utilities.main import database_connection, database_cursor

def swap_chars(s: str, i: int, j: int):
    if len(s)-1 < j:
        return s
    lst = list(s)
    lst[i],lst[j] = lst[j],lst[i]
    return "".join(lst)
