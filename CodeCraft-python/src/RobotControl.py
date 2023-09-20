import sys
import Structure
import Algorithm
import globalSetting
from collections import deque
from enum import Enum
import math

class Event:
    pass

class GetTask(Event):
    def __init__(self, task):
        self.task = task

class GotItem(Event):
    pass

class Blocked(Event):
    def __init__(self):
        pass

class UnblockedToFetch(Event):
    def __init__(self):
        pass

class UnblockedToDeliver(Event):
    def __init__(self):
        pass

class Done(Event):
    def __init__(self):
        pass

class Abandon(Event):
    def __init__(self):
        pass

class RobotController:
    pass

class RobotState:
    def Update(self, controller:RobotController):
        pass

    def React(self, event:Event, controller:RobotController):
        print("RobotState: Error passing event!")

    def React(self, event:GetTask, controller:RobotController):
        print("RobotState: Error passing event GetTask!")

    def React(self, event:GotItem, controller:RobotController):
        print("RobotState: Error passing event GotItem!")

    def React(self, event:Blocked, controller:RobotController):
        print("RobotState: Error passing event NeedToEnterAvoid!")

    def React(self, event: UnblockedToFetch, controller:RobotController):
        print("RobotState: Error passing event UnblockedToFetch!")

    def React(self, event: UnblockedToDeliver, controller:RobotController):
        print("RobotState: Error passing event UnblockedToDeliver!")

    def React(self, event: Done, controller:RobotController):
        print("RobotState: Error passing event Done!")

    def React(self, event: Abandon, controller:RobotController):
        print("RobotState: Error passing event Abandon!")

    def ToString(self):
        return "RobotState"

class Instruction:
    class Type:
        forward = 0
        rotate = 1
        buy = 2
        sell = 3
        destroy = 4

    def __init__(self, type, robot_id, value = 0.0):
        self.type = type
        self.robot_id = robot_id
        self.value = value

    def to_string(self):
        instruction_str = ""
        if self.type == self.Type.forward:
            instruction_str = "forward"
        elif self.type == self.Type.rotate:
            instruction_str = "rotate"
        elif self.type == self.Type.buy:
            instruction_str = "buy"
        elif self.type == self.Type.sell:
            instruction_str = "sell"
        elif self.type == self.Type.destroy:
            instruction_str = "destroy"

        instruction_str += " " + str(self.robot_id)

        if self.type == self.Type.forward or self.type == self.Type.rotate:
            instruction_str += " " + str(self.value)

        return instruction_str

class RobotController:
    def __init__(self, game:Structure.Game, robot_index):
        self.curState = Idle()
        self.game = game
        self.robotIndex = robot_index
        self.curTask = Structure.Task(-1, -1)
        self.instructionCache = []
        self.positionHistory = deque([Structure.Point(-100.0, -100.0)] * globalSetting.ROBOTPOSITION_HISTORY_LENGTH)
        self.orientationHistory = deque([math.pi] * globalSetting.ROBOTPOSITION_HISTORY_LENGTH)
        self.avoidExitToFetch = True

    def GameStatus(self):
        return self.game

    def RobotID(self):
        return self.robotIndex

    def GetTask(self) -> Structure.Task:
        return self.curTask

    def SetTask(self, task:Structure.Task):
        self.curTask = task

    def GetRobot(self) -> Structure.Robot:
        return self.game.robots[self.robotIndex]

    def CurState(self):
        return self.curState

    def GetInstructionCache(self):
        return self.instructionCache

    def ClearInstructionCache(self):
        self.instructionCache.clear()

    def ToFetchWorktop(self) -> Structure.Worktop:
        return self.game.worktops[self.curTask.worktopIdToFetch]

    def ToDeliverWorktop(self) -> Structure.Worktop:
        return self.game.worktops[self.game.SlotID2WorktopID(self.curTask.slogIdToDeliver)]

    def CurStateName(self):
        return "Idle"

    def TargetPosition(self):
        stateName = self.CurStateName()
        if stateName == "Fetch":
            return self.ToFetchWorktop().position
        elif stateName == "Deliver":
            return self.ToFetchWorktop().position
        else:
            return Structure.Point(0.0, 0.0)

    def Update(self):
        self.positionHistory.popleft()
        self.positionHistory.append(self.GetRobot().position)
        self.orientationHistory.popleft()
        self.orientationHistory.append(self.GetRobot().orientation)
        self.curState.Update(self)


    def GuideTo(self, target:Structure.Point):
        curRobot:Structure.Robot = self.GetRobot()
        distanceVector = Algorithm.FromTo(curRobot.position, target)
        disVecForward = math.atan2(distanceVector.y, distanceVector.x)
        theta = Algorithm.AngleDiff(curRobot.orientation, disVecForward)
        beta = curRobot.AngularAcceleration()
        tpal = theta * beta
        omega = 0.0

        if abs(tpal) > globalSetting.PALSTANCE_THRESHOLD:
            omega = -math.sqrt(tpal) if tpal >= 0.0 else math.sqrt(-tpal)

        distance = distanceVector.magnitude()
        tval = 2.0 * curRobot.Acceleration() * distance
        theoMaxVector = math.sqrt(tval)
        maxVector = theoMaxVector if theoMaxVector < 6.0 else 6.0

        if abs(theta) > (math.pi / 3):
            maxVector = 0.0
            omega = -math.pi if tpal >= 0.0 else math.pi

        self.instructionCache.append(Instruction(
            type = Instruction.Type.rotate,
            robot_id = self.robotIndex,
            value = omega
        ))

        self.instructionCache.append(Instruction(
            type = Instruction.Type.forward,
            robot_id = self.robotIndex,
            value = maxVector
        ))

    def WillCrash(self):
        for i, other in enumerate(self.game.robots):
            if i != self.RobotID():
                if Algorithm.Distance(self.GetRobot().position, other.position) < globalSetting.AVOID_DISTANCE_THRESHOLD:
                    predict = self.GetRobot().PredictPosSeq()
                    other_predict = other.PredictPosSeq()
                    for j in range(globalSetting.PREDICTSEQ_LENGTH):
                        if Algorithm.Distance(predict[j], other_predict[j]) <= \
                                (self.GetRobot().Radius() + other.Radius()) + globalSetting.CRUSH_CHECK_TOLERANCE:
                            return i

                    if abs(Algorithm.AngleDiff(self.GetRobot().orientation, other.orientation)) > globalSetting.AVOID_THETA_THRESHOLD:
                        return i
        return -1

    def CanExitAvoid(self):
        for i, other in enumerate(self.game.robots):
            if i != self.RobotID():
                if Algorithm.Distance(self.GetRobot().position, other.position) < globalSetting.EXIT_AVOID_DISTANCE:
                    predict = self.GetRobot().PredictPosSeq()
                    other_predict = other.PredictPosSeq()
                    for j in range(globalSetting.PREDICTSEQ_LENGTH):
                        if Algorithm.Distance(predict[j], other_predict[j]) < \
                                (self.GetRobot().Radius() + other.Radius()) + globalSetting.CRUSH_CHECK_TOLERANCE:
                            return False
        return True

    def TransitState(self, instance:RobotState):
        self.curState = instance

    def GetAssignedTask(self):
        return self.game.GetAssignedTask(self.robotIndex)

    def AbandonTask(self):
        self.terminate_task()
        if self.GetRobot().carryItemType != 0:
            self.instructionCache.append(Instruction(Instruction.Type.destroy, self.robotIndex, 0.0))

    def terminate_task(self):
        self.game.TerminateTask(self.curTask)

    def ContinueMovingToWorktop(self):
        self.GuideTo(self.ToFetchWorktop().position)

    def ContinueMovingToSlot(self):
        self.GuideTo(self.ToDeliverWorktop().position)

    def Spin(self):
        self.instructionCache.append(Instruction(
            type=Instruction.Type.rotate,
            robot_id=self.RobotID(),
            value=math.pi
        ))
        self.instructionCache.append(Instruction(
            type=Instruction.Type.forward,
            robot_id=self.RobotID(),
            value=1.5
        ))

    def AvoidingMove(self):
        if self.GetRobot().orientation <= 0.0:
            self.instructionCache.append(Instruction(
                type=Instruction.Type.rotate,
                robot_id=self.RobotID(),
                value=globalSetting.AVOID_OMEGA
            ))
        else:
            self.instructionCache.append(Instruction(
                type=Instruction.Type.rotate,
                robot_id=self.RobotID(),
                value=-globalSetting.AVOID_OMEGA
            ))

        self.instructionCache.append(Instruction(
            type=Instruction.Type.forward,
            robot_id=self.RobotID(),
            value=globalSetting.AVOID_VELOCITY
        ))

    def SellItem(self):
        self.instructionCache.append(Instruction(
            type = Instruction.Type.sell,
            robot_id = self.RobotID(),
            value = 0.0
        ))

    def AdjustPrice(self):
        if self.ToDeliverWorktop().type == 7:
            if Algorithm.HackerPopcnt(self.ToDeliverWorktop().materialStatus) < 2:
                for t in self.ToDeliverWorktop().config().purchaseItemTypes:
                    if (( 1 << t) & self.ToDeliverWorktop().materialStatus) == 0 \
                        and t != self.GetRobot().carryItemType:
                        self.ToDeliverWorktop().dynamicPrice[t] += globalSetting.DYNAMIC_SCORE_INCRE
                        globalSetting.DynamicScore[t] += globalSetting.DYNAMIC_SCORE_INCRE
                    else:
                        for i in range(9):
                            globalSetting.DynamicScore[i] -= self.ToDeliverWorktop().dynamicPrice[i]
                            self.ToDeliverWorktop().dynamicPrice[i] = 0.0

    def BuyItem(self):
        if self.ToFetchWorktop().productionStatus:
            self.instructionCache.append(Instruction(
                type=Instruction.Type.buy,
                robot_id = self.RobotID(),
                value=0.0
            ))
            return True
        else:
            return False

    def ReachToFetchWorktop(self):
        return self.GetRobot().worktopID == self.curTask.worktopIdToFetch

    def ReachToDeliverSlot(self):
        return self.GetRobot().worktopID == self.GameStatus().SlotID2WorktopID(self.curTask.slogIdToDeliver)

    def InStuck(self):
        return abs(Algorithm.AngleDiff(self.GetRobot().orientation, self.orientationHistory[0])) < globalSetting.ROBOTPOSITION_ANGLEDIFF_THRESHOLD \
            and Algorithm.Distance(self.GetRobot().position, self.positionHistory[0]) < globalSetting.ROBOTPOSITION_DIFF_THRESHOLD

    def NeedToEnterAvoid(self):
        will_crush_id = self.WillCrash()
        if will_crush_id != -1:
            if not self.GameStatus().robots[will_crush_id].inAvoid \
                and self.GameStatus().robots[will_crush_id].ItemPrice() > self.GetRobot().ItemPrice():
                if self.GetRobot().ItemPrice() == 0.0:
                    if Algorithm.Distance(self.GetRobot().position, self.TargetPosition()) \
                        > Algorithm.Distance(self.GameStatus().robots[will_crush_id].position, self.TargetPosition()):
                        return True
                else:
                    return True

        return False

    def NeedToLeaveAvoid(self):
        if self.CanExitAvoid():
            return True
        return False

    def SetAvoidExitToFetch(self):
        self.avoidExitToFetch = True

    def SetAvoidExitToDeliver(self):
        self.avoidExitToFetch = False

class Idle(RobotState):
    def Update(self, controller:RobotController):
        t: Structure.Task = controller.GetAssignedTask()
        # print(f'Task is {t}', file=sys.stderr)
        if t is not None and t.valid:
            controller.CurState().React(GetTask(t), controller)
        else:
            controller.Spin()
    def React(self, event:Event, controller:RobotController):
        if isinstance(event, GetTask):
            controller.SetTask(event.task)
            controller.TransitState(Fetch())


class Fetch(RobotState):
    def Update(self, controller:RobotController):
        if controller.ReachToFetchWorktop():
            if controller.BuyItem():
                controller.CurState().React(GotItem(), controller)
            else:
                controller.Spin()
        else:
            controller.ContinueMovingToWorktop()
            if controller.NeedToEnterAvoid():
                controller.CurState().React(Blocked(), controller)

    def React(self, event:Event, controller:RobotController):
        if isinstance(event, GotItem):
            controller.TransitState(Deliver())
        elif isinstance(event, Abandon):
            print("Error! Wrongly entered Abandon!")

    def ReactBlocked(self, event:Event, controller:RobotController):
        controller.SetAvoidExitToFetch()
        controller.TransitState(Avoid())

class Deliver(RobotState):
    def React(self, event:Event, controller:RobotController):
        if isinstance(event, Abandon):
            print("Error! Wrongly entered Abandon!")
        elif isinstance(event, Blocked):
            controller.SetAvoidExitToDeliver()
            controller.TransitState(Avoid())
        elif isinstance(event, Done):
            controller.terminate_task()
            controller.TransitState(Idle())

    def Update(self, controller:RobotController):
        if controller.ReachToDeliverSlot():
            print(f'robot {controller.robotIndex} deliver: ReachToDeliverSlot', file=sys.stderr)
            controller.AdjustPrice()
            controller.SellItem()
            controller.CurState().React(Done(), controller)
        else:
            controller.ContinueMovingToSlot()
            print(f'robot {controller.robotIndex} deliver: ContinueMovingToSlot', file=sys.stderr)
            if controller.NeedToEnterAvoid():
                controller.CurState().React(Blocked(), controller)


class Avoid(RobotState):
    def Update(self, controller: RobotController):
        controller.AvoidingMove()
        controller.GetRobot().inAvoid = True
        if controller.NeedToLeaveAvoid():
            print(f'robot {controller.robotIndex} avoid: NeedToLeaveAvoid', file=sys.stderr)
            controller.GetRobot().inAvoid = False
            if controller.avoidExitToFetch:
                controller.CurState().React(UnblockedToFetch(), controller)
            else:
                controller.CurState().React(UnblockedToDeliver(), controller)

    def React(self, event:Event, controller:RobotController):
        if isinstance(event, UnblockedToFetch):
            controller.TransitState(Fetch())
        elif isinstance(event, UnblockedToDeliver):
            controller.TransitState(Deliver())


class GeneralController:
    def __init__(self, game:Structure.Game):
        self.game = game
        self.controllers = []

    def Init(self):
        for i in range(len(self.game.robots)):
            self.controllers.append(RobotController(self.game, i))

    def Update(self):

        for controller in self.controllers:
            controller.Update()

    def GetOutput(self):
        instructions = []
        for controller in self.controllers:
            instructions.extend(controller.GetInstructionCache())
            controller.ClearInstructionCache()

        output = ""
        for instruction in instructions:
            output += instruction.to_string() + "\n"

        return output