import pandas as pd
import sqlite3

# 插入QuizInfo表的数据

# 读取 Excel 文件
df = pd.read_excel('quizInfo.xlsx')

# 连接到 SQLite 数据库（文件路径需与 PyCharm 中创建的路径一致）
conn = sqlite3.connect('../db/kindergarten.db')  # 修改为你的 .db 文件路径
cursor = conn.cursor()

# 将数据插入到 SQLite 表中
for i, row in df.iterrows():
    sql = "INSERT INTO QuizInfo (quiz_name, quiz_method, pass_need, sort, month_age) VALUES (?, ?, ?, ?, ?)"
    values = (row['测查项目'], row['操作方法'], row['测查通过要求'], row['项目'], row['月龄'])
    cursor.execute(sql, values)

# 提交事务并关闭连接
conn.commit()
cursor.close()
conn.close()

print("数据插入完成！")
