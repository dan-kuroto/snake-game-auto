import sys
from time import sleep, time
from queue import PriorityQueue
from random import randint, shuffle
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QMessageBox, QPushButton
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QPixmap

paths = ['space.png', 'fruit.png', '0011.png', '0101.png', '0110.png', '1001.png', '1010.png', '1100.png', '1000.png', '0100.png', '0001.png', '0010.png']  # 数字表示左右上下是否有格子
per_time = 0.01    # 刷新时间，放到文件最上面方便修改，调慢点能看清楚点


class Solve(QThread):
    refresh = pyqtSignal(list)
    hint = pyqtSignal(str)
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

    def goto(self, x: int, y: int):  # 贪吃蛇的移动+吃果子
        if self.graph[x][y] != 2:   # 没吃到果子
            self.graph[self.snake[len(self.snake) - 1][0]][self.snake[len(self.snake) - 1][1]] = 0
            self.snake.pop()
        else:
            self.fruitExist = False
            self.score += 1
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

    def a_star_search(self, x0: int, y0: int, x1: int, y1: int, getpoint: bool = True):    # A*算法
        start = (x0, y0)    # list是unhashable类型，故换元组
        goal = (x1, y1)
        border = PriorityQueue()    # 从起点开始往外探索的边界(优先级为预计消耗)
        border.put((0, start))      # 起始点的消耗为0
        lastpoint = {start: None}   # 前驱点
        nowcost = {start: 0}    # 当前已知消耗
        while not border.empty():   # 探索所有边界
            nearest = border.get()[1]   # 距离终点最近的
            if nearest == goal:
                break
            dxys = [(0, 1), (0, -1), (1, 0), (-1, 0)]
            shuffle(dxys)   # 随机排一下，免得无限循环转圈
            for dxy in dxys:
                nextp = (nearest[0] + dxy[0], nearest[1] + dxy[1])
                if not(0 <= nextp[0] <= 14 and 0 <= nextp[1] <= 14):
                    continue    # 剔除非法值
                tail = (self.snake[len(self.snake) - 1][0], self.snake[len(self.snake) - 1][1])
                if self.graph[nextp[0]][nextp[1]] == 1 and not(nextp == tail):
                    continue    # 蛇身即墙壁，除了蛇尾（不管往哪里走一步，必定会使原本的尾巴消失）
                newcost = nowcost[nearest] + 1  # 网格状，上下左右走，故增加消耗为1
                if nextp not in nowcost or newcost < nowcost[nextp]:    # 未探测或找到更低消耗
                    nowcost[nextp] = newcost
                    expcost = newcost + abs(goal[0] - nextp[0]) + abs(goal[1] - nextp[1])   # 预期消耗
                    border.put((expcost, nextp))
                    lastpoint[nextp] = nearest
        if goal not in lastpoint.keys():
            return ()
        else:
            if not getpoint:
                return nowcost[goal]
            ans = goal
            while lastpoint[ans] != start:
                ans = lastpoint[ans]
            return ans

    def search(self) -> tuple:
        to_goal = self.a_star_search(self.snake[0][0], self.snake[0][1], self.fruitPos[0], self.fruitPos[1])
        if to_goal:
            # 记录原始数据：
            graph = [[]] * 15   # 生成二维列表，长度15
            for i in range(15):
                graph[i] = self.graph[i].copy()  # 二维列表不能直接copy
            snake = []
            for part in self.snake:
                snake.append(part.copy())
            exist, score = self.fruitExist, self.score
            # 假装吃到了:模仿run方法中不断调用goto直到fruitExist为False
            while self.fruitExist:
                nextp = self.a_star_search(self.snake[0][0], self.snake[0][1], self.fruitPos[0], self.fruitPos[1])
                self.goto(nextp[0], nextp[1])
            # 在（假装）吃到之后，找尾巴
            to_tail = self.a_star_search(self.snake[0][0], self.snake[0][1], self.snake[len(self.snake) - 1][0], self.snake[len(self.snake) - 1][1])
            # 回滚
            self.graph, self.snake = graph, snake
            self.fruitExist, self.score = exist, score
            if to_tail:
                return to_goal  # 只要追着尾巴跑就永远不会死掉
        dxys = [(0, 1), (0, -1), (1, 0), (-1, 0)]
        shuffle(dxys)   # 随机排一下，免得无限循环转圈
        max_dis, ans = 0, ()
        for dxy in dxys:
            nextp = (self.snake[0][0] + dxy[0], self.snake[0][1] + dxy[1])
            if not(0 <= nextp[0] <= 14 and 0 <= nextp[1] <= 14):
                continue
            if self.graph[nextp[0]][nextp[1]] == 1 and not(nextp[0] == self.snake[len(self.snake) - 1][0] and nextp[1] == self.snake[len(self.snake) - 1][1]):
                continue
            tail = [self.snake[len(self.snake) - 1][0], self.snake[len(self.snake) - 1][1]]
            self.graph[tail[0]][tail[1]] = 0
            self.snake.pop()
            if not self.a_star_search(nextp[0], nextp[1], self.snake[len(self.snake) - 1][0], self.snake[len(self.snake) - 1][1]):
                self.graph[tail[0]][tail[1]] = 1
                self.snake.append(tail)
                continue    # 找不到尾巴的点，不能去
            self.graph[tail[0]][tail[1]] = 1
            self.snake.append(tail)
            dis = abs(nextp[0] - self.fruitPos[0]) + abs(nextp[1] - self.fruitPos[1])   # 可能走了之后就找不到果子了，所以要用估计距离
            if dis and max_dis < dis:
                max_dis = dis
                ans = nextp  # 当找不到路或走了之后就找不到尾巴（可能会死），就故意往远处走（但依然必须走完能找到尾巴）
        return ans

    def run(self):
        start = time()
        count = 0
        lasttime = time()   # 上次计算开始的时间
        for i in range(6000):   # 60s，0.01s一刷新，即共6000次
            count += 1
            lastspend = time() - lasttime
            if lastspend < per_time:
                sleep(per_time - lastspend)  # 只要上次计算时间不超过0.01s，就能靠减少睡眠时间来保证刷新速度不变（如果计算太慢也没辙）
            lasttime = time()
            if not self.fruitExist and not self.create_fruit():
                break   # 场上无果子，无法再生成果子=大获全胜
            nextpos = self.search()  # 更换了寻路算法
            if not nextpos:  # 无路可走，游戏结束
                break
            else:
                self.goto(nextpos[0], nextpos[1])
                now = time()
                self.hint.emit('（得分：{0}时间：{1:.2f}s）'.format(self.score, now - start))
                if now - start >= 60:
                    break
            self.refresh.emit([self.snake, self.fruitPos])
        print('刷新次数：{0}，实际刷新速度：{1:.4f}s/次'.format(count, (time() - start) / count))
        self.end.emit(self.score)


class GameWindow(QWidget):
    def __init__(self):
        super(GameWindow, self).__init__()
        self.setWindowTitle('贪吃蛇')
        self.setFixedSize(15 * 50, 15 * 50)
        self.pixmaps = [QPixmap(path) for path in paths]
        for i in range(len(self.pixmaps)):
            self.pixmaps[i] = self.pixmaps[i].scaled(50, 50, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        self.labels = [[QLabel(self) for i in range(15)] for j in range(15)]
        for i in range(15):
            for j in range(15):
                self.labels[i][j].setGeometry(50 * j, 50 * i, 50, 50)
                self.labels[i][j].setPixmap(self.pixmaps[0])
        self.snake = []
        self.fruit = []
        self.solve = Solve()
        self.solve.refresh.connect(self.refresh_graph)
        self.solve.hint.connect(self.refresh_title)
        self.solve.end.connect(self.game_over)
        self.startBtn = QPushButton('开始游戏', self)
        self.startBtn.resize(400, 100)
        self.startBtn.setStyleSheet('font-size: 50px;')
        self.startBtn.move((self.width() - self.startBtn.width()) // 2, (self.height() - self.startBtn.height()) // 2)
        self.startBtn.clicked.connect(self.start_game)

    def start_game(self, event):
        self.startBtn.hide()
        self.startBtn.setEnabled(False)
        self.solve.start()

    def game_over(self, score: int):
        messagebox = QMessageBox(QMessageBox.Warning, '游戏结束', '你最终获得的分数为{0}。'.format(score))
        messagebox.exec_()

    def refresh_title(self, hint: str):
        self.setWindowTitle('贪吃蛇{0}'.format(hint))

    def refresh_graph(self, data: list):
        snake, fruit = data[0], data[1]
        if self.fruit:
            self.labels[self.fruit[0]][self.fruit[1]].setPixmap(self.pixmaps[0])
        self.labels[fruit[0]][fruit[1]].setPixmap(self.pixmaps[1])
        self.fruit = fruit.copy()   # 果子位置刷新（先刷新果子，如涉及吃果子，后面刷新蛇身会覆盖）
        if self.snake:
            for part in self.snake:
                self.labels[part[0]][part[1]].setPixmap(self.pixmaps[0])
        for i in range(len(snake)):
            l, r, u, d = '0', '0', '0', '0'
            if i - 1 >= 0:
                if snake[i - 1][0] == snake[i][0] - 1 and snake[i - 1][1] == snake[i][1]:
                    l = '1'
                if snake[i - 1][0] == snake[i][0] + 1 and snake[i - 1][1] == snake[i][1]:
                    r = '1'
                if snake[i - 1][0] == snake[i][0] and snake[i - 1][1] == snake[i][1] - 1:
                    u = '1'
                if snake[i - 1][0] == snake[i][0] and snake[i - 1][1] == snake[i][1] + 1:
                    d = '1'
            if i + 1 < len(snake):
                if snake[i + 1][0] == snake[i][0] - 1 and snake[i + 1][1] == snake[i][1]:
                    l = '1'
                if snake[i + 1][0] == snake[i][0] + 1 and snake[i + 1][1] == snake[i][1]:
                    r = '1'
                if snake[i + 1][0] == snake[i][0] and snake[i + 1][1] == snake[i][1] - 1:
                    u = '1'
                if snake[i + 1][0] == snake[i][0] and snake[i + 1][1] == snake[i][1] + 1:
                    d = '1'
            index = paths.index(u + d + l + r + '.png')
            self.labels[snake[i][0]][snake[i][1]].setPixmap(self.pixmaps[index])
        self.snake = [part.copy() for part in snake]


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    sys.exit(app.exec_())
