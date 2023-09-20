import math
import sys
import globalSetting
from typing import Tuple


class ItemType:
    def __init__(self, formula, purchasePrice, originalSellPrice):
        self.formula = formula
        self.purchasePrice = purchasePrice
        self.originalSellPrice = originalSellPrice


ItemTypeDict = {
    1: ItemType([], 3000, 4000),
    2: ItemType([], 4400, 7600),
    3: ItemType([], 5800, 9200),
    4: ItemType([1, 2], 15400, 22500),
    5: ItemType([1, 3], 17200, 25000),
    6: ItemType([2, 3], 19200, 27500),
    7: ItemType([4, 5, 6], 76000, 105000)
}


def ItemSellPrice(itemType):
    if itemType not in ItemTypeDict:
        print(f"ItemSellPrice: Error! invalid item type: {itemType}")
        return None
    return ItemTypeDict[itemType].originalSellPrice


def ItemPurchasePrice(itemType):
    if itemType not in ItemTypeDict:
        print(f"ItemPurchasePrice: Error! invalid item type: {itemType}")
        return None
    return ItemTypeDict[itemType].purchasePrice


class WorktopType:
    def __init__(self, purchaseItemTypes, workCycle, produceItemType):
        self.purchaseItemTypes = purchaseItemTypes
        self.workCycle = workCycle
        self.produceItemType = produceItemType


WorktopTypeDict = {
    1: WorktopType([], 50, 1),
    2: WorktopType([], 50, 2),
    3: WorktopType([], 50, 3),
    4: WorktopType([1, 2], 500, 4),
    5: WorktopType([1, 3], 500, 5),
    6: WorktopType([2, 3], 500, 6),
    7: WorktopType([4, 5, 6], 1000, 7),
    8: WorktopType([7], 1, 0),
    9: WorktopType([1, 2, 3, 4, 5, 6, 7], 1, 0)
}


class Vector2d:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def magnitude(self):
        return math.sqrt(self.x * self.x + self.y * self.y)

    def orientation(self):
        return math.atan2(self.y, self.x)

    def __mul__(self, d):
        return Vector2d(self.x * d, self.y * d)

    def __sub__(self, other):
        return Vector2d(self.x - other.x, self.y - other.y)

    def __str__(self):
        return f"<{self.x}, {self.y}>"


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def __add__(self, other):
        if isinstance(other, Point):
            return Point(self.x + other.x, self.y + other.y)
        elif isinstance(other, Vector2d):
            return Point(self.x + other.x, self.y + other.y)
        else:
            raise ValueError("Unsupported operand type")

    def __sub__(self, other):
        if isinstance(other, Point):
            return Point(self.x - other.x, self.y - other.y)
        else:
            raise ValueError("Unsupported operand type")

    def __str__(self):
        return f"({self.x}, {self.y})"


class Robot:
    radiusIdle = 0.45
    radiusHolding = 0.53
    assumedDensity = 20.0
    assumedMaxForwardSpeed = 6.0
    assumedMaxBackwardSpeed = 2.0
    assumedMaxRotateSpeed = math.pi
    assumedMaxTractionForce = 250.0
    assumedMaxMoment = 50.0

    def __init__(self, position):
        self.worktopID = -1
        self.carryItemType = 0
        self.timeValueCoefficient = 1.0
        self.collisionValueCoefficient = 1.0
        self.palstance = 0.0
        self.velocity = Vector2d(0, 0)
        self.orientation = 0
        self.position = position
        self.inAvoid = False

    def ItemPrice(self):
        if self.carryItemType != 0:
            if self.carryItemType in ItemTypeDict:
                return (
                    self.timeValueCoefficient * self.collisionValueCoefficient
                    * ItemTypeDict[self.carryItemType].originalSellPrice
                )
            else:
                return 0.0
        else:
            return 0.0

    def SellItem(self):
        self.carryItemType = 0

    def BuyItem(self, itemType):
        self.carryItemType = itemType
        self.timeValueCoefficient = 1.0
        self.collisionValueCoefficient = 1.0

    def Radius(self):
        if self.carryItemType == 0:
            return self.radiusIdle
        else:
            return self.radiusHolding

    def Weight(self):
        return math.pi * self.Radius() * self.Radius() * self.assumedDensity

    def J(self):
        return 0.5 * self.Weight() * self.Radius() * self.Radius()

    def AngularAcceleration(self):
        return self.assumedMaxMoment / self.J()

    def Acceleration(self):
        return self.assumedMaxTractionForce / self.Weight()

    def PredictPosSeq(self):
        dx = self.velocity.x * globalSetting.PREDICTSEQ_INTERVAL
        dy = self.velocity.y * globalSetting.PREDICTSEQ_INTERVAL

        res = []
        tx = self.position.x
        ty = self.position.y

        for _ in range(globalSetting.PREDICTSEQ_LENGTH):
            tx += dx
            ty += dy
            tx = max(self.Radius(), min(tx, 50.0 - self.Radius()))  # 防止出界
            ty = max(self.Radius(), min(ty, 50.0 - self.Radius()))
            res.append(Point(tx, ty))
        return res

    def Refresh(self, worktopID, carryItemType, timeValueCoefficient, collusionCoefficient,
                palstance, velocity, orientation, position):
        self.worktopID = worktopID
        self.carryItemType = carryItemType
        self.timeValueCoefficient = timeValueCoefficient
        self.collisionValueCoefficient = collusionCoefficient
        self.palstance = palstance
        self.velocity = velocity
        self.orientation = orientation
        self.position = position

    def __str__(self):
        return (
            f"worktopID: {self.worktopID} carryingItemType: {self.carryItemType} "
            f"timeValueCoefficient: {self.timeValueCoefficient} collisionValueCoefficient: "
            f"{self.collisionValueCoefficient} palstance: {self.palstance} velocity: {self.velocity} "
            f"orientation: {self.orientation} position: {self.position}"
        )


class Worktop:
    def __init__(self, position, type):
        self.position = position
        self.type = type
        self.remainingProductionTime = -1
        self.materialStatus = 0
        self.productionStatus = False
        self.purchasingItemBits = 0
        self.producingItemType = self.config().produceItemType
        self.dynamicPrice = [0.0] * 9

        for i in self.config().purchaseItemTypes:
            self.purchasingItemBits |= (1 << i)

        if self.purchasingItemBits == 0:
            self.remainingProductionTime = self.config().workCycle

    def config(self):
        return WorktopTypeDict[self.type]

    def ProducingItemPrice(self):
        if self.producingItemType in ItemTypeDict:
            return ItemTypeDict[self.producingItemType].purchasePrice
        else:
            return 0.0

    def ItemAcceptable(self, item_type):
        return item_type != 0 and (self.purchasingItemBits & (1 << item_type)) != 0 and (self.materialStatus & (1 << item_type)) == 0

    def AcceptItem(self, item_type):
        self.materialStatus |= (1 << item_type)
        if self.materialStatus == self.purchasingItemBits or self.purchasingItemBits == 0:
            self.remainingProductionTime = self.config().workCycle
            self.materialStatus = 0

    def SellItem(self):
        self.productionStatus = False
        if self.materialStatus == self.purchasingItemBits:
            self.remainingProductionTime = self.config().workCycle
            self.materialStatus = 0

    def Interactable(self, robot):
        return (robot.carryItemType == 0 and self.productionStatus) or self.ItemAcceptable(robot.carryItemType)

    def UpdateAfterFrames(self, frames):
        if self.remainingProductionTime > frames:
            self.remainingProductionTime -= frames
        elif self.remainingProductionTime != -1:
            self.remainingProductionTime = 0

        if self.remainingProductionTime == 0:
            if not self.productionStatus:
                self.productionStatus = True
                self.remainingProductionTime = -1

        if self.materialStatus == self.purchasingItemBits:
            if not self.productionStatus:
                self.remainingProductionTime = self.config().workCycle

    def Refresh(self, type, position, remainingProductionTime, materialStatus, productionStatus):
        self.type = type
        self.position = position
        self.remainingProductionTime = remainingProductionTime
        self.materialStatus = materialStatus
        self.productionStatus = productionStatus

    def __str__(self):
        return f"position: {self.position} type: {self.type} remainingProductionTime: {self.remainingProductionTime} materialStatus: {self.materialStatus} productionStatus: {self.productionStatus}"


def EstimateWorktops(game_status, robot_index, depth):
    return []


def Direction(p1, p2):
    angle_rad = math.atan2(p2.y - p1.y, p2.x - p1.x)
    angle_deg = math.degrees(angle_rad)
    return angle_deg


class Task:
    def __init__(self, work_id_to_fetch, slot_id_to_diliver, is_valid=True):
        self.worktopIdToFetch = work_id_to_fetch
        self.slogIdToDeliver = slot_id_to_diliver
        self.valid = is_valid

    def __str__(self):
        return f"worktopIDToFetch: {self.worktopIdToFetch}, slotIDToDeliver: {self.slogIdToDeliver}, valid: {self.valid}"


class Game:
    mapSize = 50.0

    def __init__(self):
        self.curFrame = 0
        self.money = 0
        self.robots = []
        self.worktops = []
        self.slotCount = 0
        self.unassignedSlotIDs = set()
        self.unassignedToFetchWorktopIDs = set()
        self.slotID2WorktopID = {}
        self.slotID2type = {}

    def Init(self):
        
        self.InitSlots()
        print(f'unassignedSlots: {list(self.unassignedSlotIDs)}', file=sys.stderr)
        for i in range(len(self.worktops)):
            self.unassignedToFetchWorktopIDs.add(i)
            if self.worktops[i].type in {1, 2, 3}:
                self.unassignedToFetchWorktopIDs.add(i)

    def InitSlots(self):
        self.slotCount = 0
        for i in range(len(self.worktops)):
            worktop: Worktop = self.worktops[i]
            for t in worktop.config().purchaseItemTypes:
                self.unassignedSlotIDs.add(self.slotCount)
                self.unassignedToFetchWorktopIDs.add(self.slotCount)
                self.slotID2WorktopID[self.slotCount] = i
                self.slotID2type[self.slotCount] = t
                self.slotCount += 1

    def SlotID2WorktopID(self, slotID):
        if slotID in self.slotID2WorktopID:
            return self.slotID2WorktopID[slotID]
        else:
            return -1

    def SlotOccupied(self, slotID):
        worktop: Worktop = self.worktops[self.slotID2WorktopID[slotID]]
        type_ = self.slotID2type[slotID]
        return (1 << type_) & worktop.materialStatus != 0

    def SlotItemType(self, slotID):
        return self.slotID2type[slotID]

    def WorktopProducingType(self, worktopID):
        return self.worktops[worktopID].producingItemType

    def EstimateTask(status, robotID, task: Task):
        pass
    # def EstimateTask(self, robotID, task:Task):
    #     score = 0.0
    #     worktop_to_fetch_id = task.worktopIdToFetch
    #     worktop_to_deliver_id = self.SlotID2WorktopID(task.slogIdToDeliver)
    #     robot:Robot = self.robots[robotID]
    #     worktop_to_fetch:Worktop = self.worktops[worktop_to_fetch_id]
    #     worktop_to_deliver:Worktop = self.worktops[worktop_to_deliver_id]
    #     frame_of_fetching = Algorithm.EstimateFrameCost(robot.position, worktop_to_fetch.position)
    #     frame_of_delivering = Algorithm.EstimateFrameCost(worktop_to_fetch.position, worktop_to_deliver.position)
    #     worktop_to_fetch.UpdateAfterFrames(frame_of_fetching)
    #     worktop_to_deliver.UpdateAfterFrames(frame_of_fetching + frame_of_delivering)
    #
    #     if not worktop_to_fetch.productionStatus:
    #         if worktop_to_fetch.remainingProductionTime != -1:
    #             score -= globalSetting.COST_PER_FRAME * worktop_to_fetch.remainingProductionTime * 2.0
    #
    #     score -= globalSetting.COST_PER_FRAME * (frame_of_fetching + frame_of_delivering)
    #     score += worktop_to_fetch.ProducingItemPrice()
    #     score += globalSetting.DynamicScore[worktop_to_deliver.type]
    #
    #     if worktop_to_deliver.purchasingItemBits != 0:
    #         bonus_score = (worktop_to_deliver.ProducingItemPrice() + globalSetting.BONUS_SCORE_TO_DELIEVER_TO[worktop_to_deliver.type]) * \
    #             Algorithm.HackerPopcnt(int(worktop_to_deliver.materialStatus)) / \
    #             Algorithm.HackerPopcnt(int(worktop_to_deliver.purchasingItemBits))
    #         score += bonus_score
    #
    #         if worktop_to_deliver.type == 9:
    #             score -= worktop_to_fetch.ProducingItemPrice() / 3.0
    #
    #     return score

    def GetAssignedTask(self, robotID):
        print(f'unassignedIDs: {list(self.unassignedSlotIDs)}', file=sys.stderr)
        avaliableSlotIDs = [
            i for i in self.unassignedSlotIDs if not self.SlotOccupied(i)]
        # print(f'avaliableSlotID is {avaliableSlotIDs}', file=sys.stderr)

        if not avaliableSlotIDs:
            return None

        else:
            possibleTasks: [Task] = []
            for slotID in avaliableSlotIDs:
                for toFetchWorktopID in self.unassignedToFetchWorktopIDs:
                    if self.WorktopProducingType(toFetchWorktopID) == self.SlotItemType(slotID):
                        worktop: Worktop = self.worktops[toFetchWorktopID]
                        if worktop.productionStatus or worktop.remainingProductionTime != -1:
                            possibleTasks.append(Task(toFetchWorktopID, slotID))

            selectedTask = None
            if possibleTasks:
                scores = [self.EstimateTask(robotID, task)
                          for task in possibleTasks]
                p = scores.index(max(scores))
                selectedTask: Task = possibleTasks[p]
                if selectedTask.worktopIdToFetch in self.unassignedToFetchWorktopIDs:
                    self.unassignedToFetchWorktopIDs.remove(selectedTask.worktopIdToFetch)
                if selectedTask.slogIdToDeliver in self.unassignedSlotIDs:
                    self.unassignedSlotIDs.remove(selectedTask.slogIdToDeliver)

            return selectedTask

    def TerminateTask(self, task: Task):
        if task:
            self.unassignedToFetchWorktopIDs.add(task.worktopIdToFetch)
            self.unassignedSlotIDs.add(task.slogIdToDeliver)

    def TryToTrade(self, robotID, worktopID):
        worktop: Worktop = self.worktops[worktopID]
        robot: Robot = self.robots[robotID]
        if worktop.ItemAcceptable(robot.carryItemType):
            worktop.AcceptItem(robot.carryItemType)
            robot.SellItem()
            self.money += int(robot.ItemPrice())

        if worktop.productionStatus and self.money > worktop.ProducingItemPrice() and robot.carryItemType == 0:
            worktop.SellItem()
            robot.BuyItem(worktop.producingItemType)
            self.money -= int(worktop.ProducingItemPrice())

    def ApplySelection(self, robotIndex, worktopIndex):
        cur_robot: Robot = self.robots[robotIndex]
        cur_worktop: Worktop = self.worktops[worktopIndex]

        cur_robot.orientation = Direction(
            cur_robot.position, cur_worktop.position)
        cur_robot.position = cur_worktop.position
        self.TryToTrade(robotIndex, worktopIndex)

    def LoadRobot(self, x, y):
        self.robots.append(Robot(Point(x, y)))

    def LoadWorktop(self, x, y, type_):
        new_worktop = Worktop(Point(x, y), type_)
        self.worktops.append(new_worktop)

    def RefreshCurrentFrameId(self, frameID):
        self.curFrame = frameID

    def RefreshCurrentMoney(self, curmoney):
        self.money = curmoney

    def RefreshWorktopStatus(self, index, type_, x, y, remainingProductionTime, materialStatus, productionStatus):
        self.worktops[index].Refresh(type_, Point(
            x, y), remainingProductionTime, materialStatus, productionStatus)

    def RefreshRobotStatus(self, index, worktopID, carryingItemType, timeCof, collusionCof, palstance, vx, vy, orientation, x, y):
        self.robots[index].Refresh(worktopID, carryingItemType, timeCof,
                                   collusionCof, palstance, Vector2d(vx, vy), orientation, Point(x, y))

    def __str__(self):
        result = f"curFrame: {self.curFrame} money: {self.money}\nRobots:\n"
        for i, p in enumerate(self.robots):
            result += f"Robot No.{i}:\n\t{p}\n"
        result += "\nWorktops:\n"
        for i, p in enumerate(self.worktops):
            result += f"Worktop No.{i}:\n\t{p}\n"
        return result
