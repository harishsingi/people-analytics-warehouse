"""Close the current SCD2 row and open a new one when an attribute changes."""
def apply_change(current, new_dept, change_date):
    if current["department"]==new_dept: return [current]
    closed={**current,"valid_to":change_date,"is_current":0}
    opened={"employee_id":current["employee_id"],"department":new_dept,"valid_from":change_date,"valid_to":None,"is_current":1}
    return [closed,opened]
if __name__=="__main__":
    print(apply_change({"employee_id":"E1","department":"Eng","valid_from":"2024-01-01","valid_to":None,"is_current":1},"Data","2025-03-01"))
