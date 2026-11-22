import sqlite3, random
random.seed(3)
con=sqlite3.connect("people.db"); con.execute("DROP TABLE IF EXISTS employees"); con.execute("CREATE TABLE employees (id INTEGER, dept TEXT, tenure_months INTEGER, exited INTEGER)")
for i in range(500): con.execute("INSERT INTO employees VALUES (?,?,?,?)",(i,random.choice(["Eng","Sales","Ops","Finance"]),random.randint(1,120),1 if random.random()<0.14 else 0))
con.commit(); print("loaded 500 synthetic employees")
