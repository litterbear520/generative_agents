"""
作者: Joon Sung Park (joonspk@stanford.edu)

文件: spatial_memory.py
描述: 定义 MemoryTree 类，作为智能体的空间记忆，有助于将其行为
      基于游戏世界进行定位。
"""
import json
import sys
sys.path.append('../../')

from utils import *
from global_methods import *

class MemoryTree: 
  def __init__(self, f_saved): 
    self.tree = {}
    if check_if_file_exists(f_saved): 
      self.tree = json.load(open(f_saved))


  def print_tree(self): 
    def _print_tree(tree, depth):
      dash = " >" * depth
      if type(tree) == type(list()): 
        if tree:
          print (dash, tree)
        return 

      for key, val in tree.items(): 
        if key: 
          print (dash, key)
        _print_tree(val, depth+1)
    
    _print_tree(self.tree, 0)
    

  def save(self, out_json):
    with open(out_json, "w") as outfile:
      json.dump(self.tree, outfile) 



  def get_str_accessible_sectors(self, curr_world): 
    """
    返回智能体在当前区域内可以访问的所有竞技场的摘要字符串。

    注意有些地方给定的智能体无法进入。这些信息在智能体表单中提供。
    我们在此函数中考虑了这一点。

    输入
      None
    输出 
      智能体可以访问的所有竞技场的摘要字符串。
    示例字符串输出
      "bedroom, kitchen, dining room, office, bathroom"
    """
    x = ", ".join(list(self.tree[curr_world].keys()))
    return x


  def get_str_accessible_sector_arenas(self, sector): 
    """
    返回智能体在当前区域内可以访问的所有竞技场的摘要字符串。

    注意有些地方给定的智能体无法进入。这些信息在智能体表单中提供。
    我们在此函数中考虑了这一点。

    输入
      None
    输出 
      智能体可以访问的所有竞技场的摘要字符串。
    示例字符串输出
      "bedroom, kitchen, dining room, office, bathroom"
    """
    curr_world, curr_sector = sector.split(":")
    if not curr_sector: 
      return ""
    x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))
    return x


  def get_str_accessible_arena_game_objects(self, arena):
    """
    获取竞技场中所有可访问游戏对象的字符串列表。如果指定了 temp_address，
    我们返回该竞技场中可用的对象，如果没有，我们返回智能体当前所在
    竞技场中的对象。

    输入
      temp_address: 可选的竞技场地址
    输出 
      游戏竞技场中所有可访问游戏对象的字符串列表。
    示例字符串输出
      "phone, charger, bed, nightstand"
    """
    curr_world, curr_sector, curr_arena = arena.split(":")

    if not curr_arena: 
      return ""

    try: 
      x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena]))
    except: 
      x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena.lower()]))
    return x


if __name__ == '__main__':
  x = f"../../../../environment/frontend_server/storage/the_ville_base_LinFamily/personas/Eddy Lin/bootstrap_memory/spatial_memory.json"
  x = MemoryTree(x)
  x.print_tree()

  print (x.get_str_accessible_sector_arenas("dolores double studio:double studio"))







