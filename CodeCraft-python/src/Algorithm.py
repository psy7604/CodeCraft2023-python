import Structure
import globalSetting
import math
import importlib

game = Structure.Game()

def Distance(p1:Structure.Point, p2:Structure.Point):
    return math.sqrt((p1.x - p2.x) ** 2 + (p1.y - p2.y) ** 2)

def custom_sub(p1:Structure.Point, p2:Structure.Point):
    return Structure.Vector2d(p2.x - p1.x, p2.y - p1.y)

Structure.Vector2d.__sub__ = custom_sub

def FromTo(p1:Structure.Point, p2:Structure.Point) -> Structure.Vector2d:
    return Structure.Vector2d(p2.x - p1.x, p2.y - p1.y)

def Direction(p1:Structure.Point, p2:Structure.Point):
    # return FromTo(p1, p2).Orientation()
    return FromTo(p1, p2)

def AngleDiff(a1, a2):
    angleDiff = a1 - a2
    if abs(angleDiff) > math.pi:
        if angleDiff < 0.0:
            angleDiff += 2.0 * math.pi
        else:
            angleDiff -= 2.0 * math.pi
    return angleDiff

def RobotWorktopAngleDiff(robot:Structure.Robot, worktop:Structure.Worktop):
    r2w = math.atan2(worktop.position.y - robot.position.y, worktop.position.x - robot.position.x)
    robot_dir = robot.orientation
    angle_diff = robot_dir - r2w
    if abs(angle_diff) > math.pi:
        if angle_diff < 0.0:
            angle_diff += 2.0 * math.pi
        else:
            angle_diff -= 2.0 * math.pi
    return angle_diff

def Estimate(gameStatus:Structure.Game):
    res = 0.0
    res -= gameStatus.curFrame * globalSetting.COST_PER_FRAME
    res += gameStatus.money
    for robot in gameStatus.robots:
        res += robot.ItemPrice()
    return res

def EstimateFrameCost(startPoint:Structure.Point, targetPoint:Structure.Point):
    assumed_velocity = globalSetting.ASSUMED_ROBOT_VELOCITY
    time_per_frame = globalSetting.TIME_PER_FRAME

    distance = math.sqrt((startPoint.x - targetPoint.x) ** 2 + (startPoint.y - targetPoint.y) ** 2)
    res = int(distance / (assumed_velocity * time_per_frame))
    return res

def HackerPopcnt(n):
    n -= (n >> 1) & 0x55555555
    n = (n & 0x33333333) + ((n >> 2) & 0x33333333)
    n = ((n >> 4) + n) & 0x0F0F0F0F
    n += n >> 8
    n += n >> 16
    return n & 0x0000003F


def EstimateTaskNew(status, robotID, task:Structure.Task):
    score = 0.0
    worktop_to_fetch_id = task.worktopIdToFetch
    worktop_to_deliver_id = status.SlotID2WorktopID(task.slogIdToDeliver)
    robot:Structure.Robot = status.robots[robotID]
    worktop_to_fetch:Structure.Worktop = status.worktops[worktop_to_fetch_id]
    worktop_to_deliver:Structure.Worktop = status.worktops[worktop_to_deliver_id]
    frame_of_fetching = EstimateFrameCost(robot.position, worktop_to_fetch.position)
    frame_of_delivering = EstimateFrameCost(worktop_to_fetch.position, worktop_to_deliver.position)
    worktop_to_fetch.UpdateAfterFrames(frame_of_fetching)
    worktop_to_deliver.UpdateAfterFrames(frame_of_fetching + frame_of_delivering)

    if not worktop_to_fetch.productionStatus:
        if worktop_to_fetch.remainingProductionTime != -1:
            score -= globalSetting.COST_PER_FRAME * worktop_to_fetch.remainingProductionTime * 2.0

    score -= globalSetting.COST_PER_FRAME * (frame_of_fetching + frame_of_delivering)
    score += worktop_to_fetch.ProducingItemPrice()
    score += globalSetting.DynamicScore[worktop_to_deliver.type]

    if worktop_to_deliver.purchasingItemBits != 0:
        bonus_score = (worktop_to_deliver.ProducingItemPrice() + globalSetting.BONUS_SCORE_TO_DELIEVER_TO[worktop_to_deliver.type]) * \
            HackerPopcnt(int(worktop_to_deliver.materialStatus)) / \
            HackerPopcnt(int(worktop_to_deliver.purchasingItemBits))
        score += bonus_score

        if worktop_to_deliver.type == 9:
            score -= worktop_to_fetch.ProducingItemPrice() / 3.0

    return score

Structure.Game.EstimateTask = EstimateTaskNew





