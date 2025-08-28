"""
作者: Joon Sung Park (joonspk@stanford.edu)

文件: execute.py
描述: 定义生成式智能体的"执行"模块。
"""
import sys
import random
sys.path.append('../../')

from global_methods import *
from path_finder import *
from utils import *

def execute(persona, maze, personas, plan): 
  """
  给定一个计划（动作的字符串地址），我们执行该计划（实际输出瓦片坐标路径
  和智能体的下一个坐标）。

  输入:
    persona: 当前 <Persona> 实例。
    maze: 当前 <Maze> 的实例。
    personas: 世界中所有智能体的字典。
    plan: 这是我们需要执行的动作的字符串地址。
       它的形式为 "{world}:{sector}:{arena}:{game_objects}"。
       重要的是，你不能使用负索引（例如 [-1]）来访问它，因为在某些情况下
       后面的地址元素可能不存在。
       例如："dolores double studio:double studio:bedroom 1:bed"
    
  输出: 
    execution
  """
  if "<random>" in plan and persona.scratch.planned_path == []: 
    persona.scratch.act_path_set = False

  # 如果为当前动作设置了路径，则 <act_path_set> 设置为 True。
  # 否则为 False，意味着我们需要构建一个新路径。
  if not persona.scratch.act_path_set: 
    # <target_tiles> 是智能体可能前往执行当前动作的瓦片坐标列表。
    # 目标是从中选择一个。
    target_tiles = None

    print ('aldhfoaf/????')
    print (plan)

    if "<persona>" in plan: 
      # 执行智能体间的交互。
      target_p_tile = (personas[plan.split("<persona>")[-1].strip()]
                       .scratch.curr_tile)
      potential_path = path_finder(maze.collision_maze, 
                                   persona.scratch.curr_tile, 
                                   target_p_tile, 
                                   collision_block_id)
      if len(potential_path) <= 2: 
        target_tiles = [potential_path[0]]
      else: 
        potential_1 = path_finder(maze.collision_maze, 
                                persona.scratch.curr_tile, 
                                potential_path[int(len(potential_path)/2)], 
                                collision_block_id)
        potential_2 = path_finder(maze.collision_maze, 
                                persona.scratch.curr_tile, 
                                potential_path[int(len(potential_path)/2)+1], 
                                collision_block_id)
        if len(potential_1) <= len(potential_2): 
          target_tiles = [potential_path[int(len(potential_path)/2)]]
        else: 
          target_tiles = [potential_path[int(len(potential_path)/2+1)]]
    
    elif "<waiting>" in plan: 
      # 执行智能体决定在执行其动作之前等待的交互。
      x = int(plan.split()[1])
      y = int(plan.split()[2])
      target_tiles = [[x, y]]

    elif "<random>" in plan: 
      # 执行随机位置动作。
      plan = ":".join(plan.split(":")[:-1])
      target_tiles = maze.address_tiles[plan]
      target_tiles = random.sample(list(target_tiles), 1)

    else: 
      # 这是我们的默认执行。我们简单地将智能体带到当前动作发生的位置。
      # 检索目标地址。再次说明，plan 是字符串形式的动作地址。
      # <maze.address_tiles> 接受这个并返回候选坐标。 
      if plan not in maze.address_tiles: 
        maze.address_tiles["Johnson Park:park:park garden"] #ERRORRRRRRR
      else: 
        target_tiles = maze.address_tiles[plan]

    # 有时会从中返回多个瓦片（例如，一张桌子可能跨越许多坐标）。
    # 所以，我们在这里采样一些。从那个随机样本中，我们将取最近的那些。 
    if len(target_tiles) < 4: 
      target_tiles = random.sample(list(target_tiles), len(target_tiles))
    else:
      target_tiles = random.sample(list(target_tiles), 4)
    # 如果可能的话，我们希望智能体在前往迷宫中的同一位置时占据不同的瓦片。
    # 如果它们最终在同一时间到达是可以的，但我们尝试降低这种概率。
    # 我们在这里处理这种重叠。  
    persona_name_set = set(personas.keys())
    new_target_tiles = []
    for i in target_tiles: 
      curr_event_set = maze.access_tile(i)["events"]
      pass_curr_tile = False
      for j in curr_event_set: 
        if j[0] in persona_name_set: 
          pass_curr_tile = True
      if not pass_curr_tile: 
        new_target_tiles += [i]
    if len(new_target_tiles) == 0: 
      new_target_tiles = target_tiles
    target_tiles = new_target_tiles

    # 现在我们已经确定了目标瓦片，我们找到到其中一个目标瓦片的最短路径。 
    curr_tile = persona.scratch.curr_tile
    collision_maze = maze.collision_maze
    closest_target_tile = None
    path = None
    for i in target_tiles: 
      # path_finder 接受 collision_maze 和 curr_tile 坐标作为输入，
      # 并返回成为路径的坐标元组列表。
      # 例如：[(0, 1), (1, 1), (1, 2), (1, 3), (1, 4)...]
      curr_path = path_finder(maze.collision_maze, 
                              curr_tile, 
                              i, 
                              collision_block_id)
      if not closest_target_tile: 
        closest_target_tile = i
        path = curr_path
      elif len(curr_path) < len(path): 
        closest_target_tile = i
        path = curr_path

    # 实际设置 <planned_path> 和 <act_path_set>。我们切掉 planned_path 中的
    # 第一个元素，因为它包含 curr_tile。
    persona.scratch.planned_path = path[1:]
    persona.scratch.act_path_set = True
  
  # 设置下一个直接步骤。如果没有剩余的 <planned_path>，我们停留在 curr_tile，
  # 否则，我们前往路径中的下一个瓦片。
  ret = persona.scratch.curr_tile
  if persona.scratch.planned_path: 
    ret = persona.scratch.planned_path[0]
    persona.scratch.planned_path = persona.scratch.planned_path[1:]

  description = f"{persona.scratch.act_description}"
  description += f" @ {persona.scratch.act_address}"

  execution = ret, persona.scratch.act_pronunciatio, description
  return execution















