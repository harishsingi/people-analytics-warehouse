from src.scd2_demo import apply_change
def test_scd2_closes_and_opens():
    out=apply_change({"employee_id":"E1","department":"Eng","valid_from":"2024-01-01","valid_to":None,"is_current":1},"Data","2025-03-01")
    assert out[0]["is_current"]==0 and out[1]["department"]=="Data"
