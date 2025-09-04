"""
描述: 定义 MemoryTree 类，作为智能体的空间记忆，有助于将其行为
      基于游戏世界进行定位。
"""
import json
import sys
sys.path.append('../../')

from utils import *
from global_methods import *

# 空间记忆树类：用于存储和管理智能体的空间记忆信息
class MemoryTree: 
  # 初始化空间记忆树
  def __init__(self, f_saved): 
    self.tree = {}                                     # 初始化空的树结构，是一个字典
    if check_if_file_exists(f_saved):                  # 检查是否存在保存的文件
      self.tree = json.load(open(f_saved))             # 如果存在则从文件加载记忆树


  # 打印整个记忆树结构
  # 举例：对 Maria Lopez 的记忆树调用 print_tree() 会输出：
  # the Ville
  #  > Oak Hill College
  #  >> hallway
  #  >> library
  #  >>> ['library sofa', 'library table', 'bookshelf']
  #  >> classroom
  #  >>> ['blackboard', 'classroom podium', 'classroom student seating']
  #  > Dorm for Oak Hill College
  #  >> garden
  #  >>> ['dorm garden']
  #  >> Maria Lopez's room
  #  >>> ['closet', 'desk', 'bed', 'computer', 'blackboard']
  def print_tree(self): 
    # 递归打印树结构的内部函数,输入参数是树结构字典和深度
    def _print_tree(tree, depth):
      dash = " >" * depth                             # 根据深度创建缩进标识
      if type(tree) == type(list()):                 # 如果是列表类型
        if tree:                                     # 如果列表不为空
          print (dash, tree)                         # 打印列表内容
        return                                       # 返回，结束递归

      for key, val in tree.items():                 # 遍历树的每个键值对
        if key:                                      # 如果键不为空
          print (dash, key)                          # 打印键名
        _print_tree(val, depth+1)                   # 递归打印值，深度加1
    
    _print_tree(self.tree, 0)                       # 从根节点开始打印，深度为0
    

  # 保存记忆树到JSON文件
  def save(self, out_json):
    with open(out_json, "w") as outfile:            # 打开输出文件进行写入
      json.dump(self.tree, outfile)                 # 将树结构保存为JSON格式 

  # 城市：区域：场所：对象
  # 获取当前城市中智能体可访问的所有区域
  def get_str_accessible_sectors(self, curr_world): 

    x = ", ".join(list(self.tree[curr_world].keys()))  # 获取当前世界下所有区域的键，用逗号连接
    return x                                           # 返回区域名称字符串


  # 城市：区域：场所：对象
  # 获取指定区域中智能体可访问的所有场所
  def get_str_accessible_sector_arenas(self, sector): 

    curr_world, curr_sector = sector.split(":")       # 将区域地址按冒号分割为世界名和区域名
    if not curr_sector:                               # 如果区域名为空
      return ""                                       # 返回空字符串
    x = ", ".join(list(self.tree[curr_world][curr_sector].keys()))  # 获取指定区域下所有场所的键，用逗号连接
    return x                                          # 返回场所名称字符串


  # 城市：区域：场所：对象
  # 获取指定场所中智能体可访问的所有对象，对象可以是场所内的物品、人、动物等
  def get_str_accessible_arena_game_objects(self, arena):

    curr_world, curr_sector, curr_arena = arena.split(":")  # 将场所地址按冒号分割为世界、区域、场所

    if not curr_arena:                                      # 如果场所名为空
      return ""                                             # 返回空字符串

    try:                                                    # 尝试获取对象
      x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena]))  # 获取场所中所有对象，用逗号连接
    except:                                                 # 如果失败（可能是大小写问题）
      x = ", ".join(list(self.tree[curr_world][curr_sector][curr_arena.lower()]))  # 尝试使用小写的场所名
    return x                                                # 返回对象名称字符串


# 主程序入口：用于测试和示例
if __name__ == '__main__':
  x = f"../../../../environment/frontend_server/storage/the_ville_base_LinFamily/personas/Eddy Lin/bootstrap_memory/spatial_memory.json"  # 设置测试文件路径
  x = MemoryTree(x)                                     # 创建记忆树实例
  x.print_tree()                                        # 打印整个记忆树结构

  print (x.get_str_accessible_sector_arenas("dolores double studio:double studio"))  # 测试获取指定区域的场所







