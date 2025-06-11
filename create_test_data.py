import pandas as pd

# 创建测试数据
data = {
    '产品名称': ['智能手机', '笔记本电脑', '平板电脑', '智能手表'],
    '价格': [3999, 6999, 2999, 1999],
    '库存': [100, 50, 80, 120],
    '描述': [
        '最新款智能手机，搭载高通骁龙处理器，6.7英寸OLED屏幕，支持5G网络。',
        '轻薄商务本，Intel i7处理器，16GB内存，512GB固态硬盘，15.6英寸高清屏。',
        '10.9英寸视网膜屏幕，A14仿生芯片，支持第二代Apple Pencil，续航持久。',
        '多功能运动手表，心率监测，GPS定位，50米防水，支持多种运动模式。'
    ]
}

# 创建DataFrame
df = pd.DataFrame(data)

# 保存为Excel文件
df.to_excel('test_data.xlsx', index=False)

print("Excel文件已创建：test_data.xlsx") 