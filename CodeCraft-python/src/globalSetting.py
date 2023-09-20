import math

# 帧率设置
FRAME_PER_SECOND = 50
TOTAL_FRAMES = 50 * 3 * 60
SEARCH_DEPTH = 0
TIME_PER_FRAME = 1 / FRAME_PER_SECOND

# 物品价值数组
ITEM_VALUES = [0, 3000, 3200, 3400, 7100, 7800, 8300, 29000]

COST_PER_FRAME = 112.2

# 假定的机器人线速度和角速度
ASSUMED_ROBOT_VELOCITY = 5.8
ASSUMED_ROBOT_PALSTANCE = math.pi

PALSTANCE_THRESHOLD = 0.0

# 无法互动的工作台分数惩罚
UNINTERACTABLE_PANELTY = -50000000.0 - TOTAL_FRAMES * COST_PER_FRAME

# 保存的机器人位置历史长度（用于判断是否卡住）
ROBOTPOSITION_HISTORY_LENGTH = 20

# 机器人位置之差阈值（用于判断是否卡住）
ROBOTPOSITION_DIFF_THRESHOLD = 0.2

# 机器人角度之差阈值（用于判断是否卡住）
ROBOTPOSITION_ANGLEDIFF_THRESHOLD = 0.10

# 进入避障的临界距离阈值
AVOID_DISTANCE_THRESHOLD = 6.0

# 退出避障的最小相隔距离
EXIT_AVOID_DISTANCE = 3.0

# 碰撞检测的容差
CRUSH_CHECK_TOLERANCE = 0.01

# 判断为迎面相撞的临界角度
AVOID_THETA_THRESHOLD = math.pi * 4.0 / 5.0

# 避障给的角速度
AVOID_OMEGA = math.pi

# 避障给的线速度
AVOID_VELOCITY = 4.0

# 预测位置序列的长度和时间间隔
PREDICTSEQ_LENGTH = 10
PREDICTSEQ_INTERVAL = 0.1

# 交付给工作台的奖励分数数组
BONUS_SCORE_TO_DELIEVER_TO = [0.0, 0.0, 0.0, 0.0, 5000.0, 5000.0, 5000.0, 37777.0, 0.0, 0.0]

# 动态分数数组
DynamicScore = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
DYNAMIC_SCORE_INCRE = 5000.0