import sys
import Structure
import RobotControl


game = Structure.Game()
generalController = RobotControl.GeneralController(game)

# def read_util_ok():         # 该函数用于读取输入直到得到一个OK
#     while True:
#         line = input().strip()
#         if line == "OK":
#             return True
#     return False

def load_map(game):
    row = 0
    suc = False
    while True:
        line = input().strip()
        if line == "OK":
            suc = True
            break

        for i, char in enumerate(line):
            if char == '.':
                pass
            elif char == 'A':
                game.LoadRobot(0.25 + 0.5 * i, 49.75 - 0.5 * row)
            elif '1' <= char <= '9':
                worktop_type = int(char)
                game.LoadWorktop(0.25 + 0.5 * i, 49.75 - 0.5 * row, worktop_type)
            else:
                pass

        row += 1

    return suc


def load_frame(game):
    # current_money, K = map(int, input().split())
    K = int(input())

    for i in range(K):
        worktop_type, worktop_posx, worktop_posy, remaining_production_time, material_status, production_status = map(float, input().split())
        game.RefreshWorktopStatus(i, int(worktop_type), worktop_posx, worktop_posy, int(remaining_production_time), int(material_status), int(production_status))

    for i in range(4):
        cur_worktop_id, carrying_item_type, time_value_coefficient, collision_value_coefficient, palstance, vx, vy, orientation, px, py = map(float, input().split())
        game.RefreshRobotStatus(i, int(cur_worktop_id), int(carrying_item_type), time_value_coefficient, collision_value_coefficient, palstance, vx, vy, orientation, px, py)

    temp = input().strip()
    return temp == "OK"


def main():
    load_map(game)
    print("OK")
    sys.stdout.flush()

    generalController.Init()
    frame_count = 0
    game.Init()

    while True:
        try:
            frame_input = input()
            frame_data = frame_input.split()
            if not frame_data:
                break
            frame_id = int(frame_data[0])
            game.RefreshCurrentFrameId(frame_id)
            if not load_frame(game):
                break

            for rc in generalController.controllers:
                print(type(rc.curState), file=sys.stderr)
            generalController.Update()
            print(frame_id)
            cache = generalController.GetOutput()
            sys.stdout.write(cache)
            print("OK")
            print(cache, file=sys.stderr)
            sys.stdout.flush()

            frame_count += 1
        except EOFError:
            break


if __name__ == '__main__':
    main()