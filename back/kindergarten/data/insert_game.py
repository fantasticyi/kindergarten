import pandas as pd
import sqlite3

# 插入Game表的数据

# 读取Excel文件
df = pd.read_excel('game.xlsx', sheet_name='Sheet1')

# 映射游戏分类到数字
game_sort_mapping = {
    '大运动': 1,
    '精细动作': 2,
    '语言': 3,
    '适应能力': 4,
    '社会行为': 5
}

# 应用分类映射
df['game_sort_num'] = df['game_sort'].map(game_sort_mapping).fillna(1)  # 默认为1如果找不到映射

# 连接到SQLite数据库
conn = sqlite3.connect('../db/kindergarten.db')  # 修改为你的.db文件路径
cursor = conn.cursor()

# 将数据插入到SQLite表中
for i, row in df.iterrows():
    sql = """
    INSERT INTO Game (
        game_name, game_sort, game_beginTime, game_endTime, 
        game_bg, game_prepare, game_purpose, game_process, cautions
    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    values = (
        row['game_name'],
        int(row['game_sort_num']),  # 确保转换为整数
        int(row['game_beginTime']),
        int(row['game_endTime']),
        row['game_bg'] if pd.notna(row['game_bg']) else '',
        row['game_prepare'] if pd.notna(row['game_prepare']) else '',
        row['game_purpose'] if pd.notna(row['game_purpose']) else '',
        row['game_process'] if pd.notna(row['game_process']) else '',
        row['cautions'] if pd.notna(row['cautions']) else ''
    )
    cursor.execute(sql, values)

# 提交事务并关闭连接
conn.commit()
cursor.close()
conn.close()

print("数据插入完成！")
