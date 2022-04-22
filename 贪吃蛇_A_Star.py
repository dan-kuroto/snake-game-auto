import sys
from time import sleep
from queue import PriorityQueue
from random import randint
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox
from PyQt5.QtCore import QThread, pyqtSignal

color = ['white', 'black', 'lightgreen']    # 空、蛇、果，对应的颜色
per_time = 0.01    # 刷新时间，放到文件最上面方便修改，调慢点能看清楚点


class Solve(QThread):
    fresh = pyqtSignal(list)
    scored = pyqtSignal(int)
    end = pyqtSignal(int)

    def __init__(self):
        super(Solve, self).__init__()
        self.graph = [[0 for i in range(15)] for j in range(15)]
        for i in range(3):
            self.graph[0][i] = 1    # 地图，0-空，1-蛇，2-果
        self.snake = [[0, 2], [0, 1], [0, 0]]   # 初始蛇身
        self.score = 0
        self.fruitExist = False
        self.fruitPos = [0, 0]
        self.scoreUp = False    # 得分升高

    def goto(self, x: int, y: int):  # 贪吃蛇的移动+吃果子
        if self.graph[x][y] != 2:   # 没吃到果子
            self.graph[self.snake[len(self.snake) - 1][0]][self.snake[len(self.snake) - 1][1]] = 0
            self.snake.pop()
        else:
            self.fruitExist = False
            self.score += 1
            self.scoreUp = True
        self.graph[x][y] = 1
        self.snake.insert(0, [x, y])

    def create_fruit(self):
        ground = 15 * 15 - 3 - self.score   # 空闲位置数
        if ground < 1:
            return False
        index = randint(1, ground)
        count = 0
        flag = True
        for i in range(15):
            for j in range(15):
                if self.graph[i][j] == 0:
                    count += 1
                    if count == index:  # 这个if可以不嵌套，但嵌套一下可以减少判断次数
                        self.graph[i][j] = 2
                        self.fruitExist = True
                        self.fruitPos = [i, j]
                        flag = False
                        break
            if not flag:
                break
        return True

    def a_star_search(self) -> tuple:   # A*算法
        start = (self.snake[0][0], self.snake[0][1])    # list是unhashable类型，故换元组
        goal = (self.fruitPos[0], self.fruitPos[1])
        border = PriorityQueue()    # 从起点开始往外探索的边界(优先级为预计消耗)
        border.put((0, start))      # 起始点的消耗为0
        lastpoint = {start: None}   # 前驱点
        nowcost = {start: 0}    # 当前已知消耗
        while not border.empty():   # 探索所有边界
            nearest = border.get()[1]   # 距离终点最近的
            if nearest == goal:
                break
            for dxy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                nextp = (nearest[0] + dxy[0], nearest[1] + dxy[1])
                if not(0 <= nextp[0] <= 14 and 0 <= nextp[1] <= 14):
                    continue    # 剔除非法值
                if self.graph[nextp[0]][nextp[1]] == 1:
                    continue    # 蛇身即墙壁
                newcost = nowcost[nearest] + 1  # 网格状，上下左右走，故增加消耗为1
                if nextp not in nowcost or newcost < nowcost[nextp]:    # 未探测或找到更低消耗
                    nowcost[nextp] = newcost
                    expcost = newcost + abs(goal[0] - nextp[0]) + abs(goal[1] - nextp[1])   # 预期消耗
                    border.put((expcost, nextp))
                    lastpoint[nextp] = nearest
        if goal not in lastpoint.keys():
            mincost, ans = float('INF'), ()  # 如果四个方向都不能走的话返回空元组，表示死亡
            for dxy in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
                tempp = (start[0] + dxy[0], start[1] + dxy[1])
                if not(0 <= tempp[0] <= 14 and 0 <= tempp[1] <= 14):
                    continue
                if self.graph[tempp[0]][tempp[1]] == 1:
                    continue
                if nowcost[tempp] < mincost:
                    mincost = nowcost[tempp]
                    ans = tempp  # 尽量找更接近的
            return ans
        else:
            ans = goal
            while lastpoint[ans] != start:
                ans = lastpoint[ans]
            return ans

    def run(self):
        for i in range(6000):   # 60s，0.01s一刷新，即共6000次
            sleep(per_time)
            if not self.fruitExist and not self.create_fruit():
                break   # 场上无果子，无法再生成果子=大获全胜
            nextpos = self.a_star_search()  # 似乎是这里的问题
            if not nextpos:  # 无路可走，游戏结束
                break
            else:
                self.goto(nextpos[0], nextpos[1])
                if self.scoreUp:
                    self.scored.emit(self.score)
                    self.scoreUp = False
            self.fresh.emit(self.graph)
        self.end.emit(self.score)


class GameWindow(QWidget):
    def __init__(self):
        super(GameWindow, self).__init__()
        self.setWindowTitle('贪吃蛇')
        self.setFixedSize(15 * 50, 15 * 50)
        self.labels = [[QLabel(self) for i in range(15)] for j in range(15)]
        for i in range(15):
            for j in range(15):
                self.labels[i][j].setGeometry(50 * j, 50 * i, 50, 50)
        self.solve = Solve()
        self.solve.fresh.connect(self.refresh_screen)
        self.solve.scored.connect(self.refresh_title)
        self.solve.end.connect(self.game_over)
        self.solve.start()

    def game_over(self, score: int):
        messagebox = QMessageBox(QMessageBox.Warning, '游戏结束', '你最终获得的分数为{0}。'.format(score))
        messagebox.exec_()

    def refresh_title(self, score):
        self.setWindowTitle('贪吃蛇（得分：{0}）'.format(score))

    def refresh_screen(self, graph: list):
        for i in range(15):
            for j in range(15):
                self.labels[i][j].setStyleSheet('background-color:%s;' % color[graph[i][j]])


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec_())
