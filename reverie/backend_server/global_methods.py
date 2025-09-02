import random      # 随机数生成
import string      # 字符串操作工具
import csv         # CSV文件处理
import time        # 时间相关操作
import datetime as dt  # 日期时间处理
import pathlib     # 路径操作（面向对象）
import os          # 操作系统接口
import sys         # 系统相关参数和函数
import numpy       # 数值计算库
import math        # 数学函数
import shutil, errno   # 高级文件操作和错误处理

from os import listdir  # 目录内容列表

# 创建目录，如果目录不存在则创建
def create_folder_if_not_there(curr_path): 

  outfolder_name = curr_path.split("/")   # 将路径按 "/" 分割成组件列表
  
  if len(outfolder_name) != 1:            # 检查路径是指向文件还是目录
    if "." in outfolder_name[-1]:         # 如果最后一个组件包含 "."，则认为是文件，需要去掉文件名
      outfolder_name = outfolder_name[:-1]

    # 重新组合目录路径
    outfolder_name = "/".join(outfolder_name)
    
    # 检查目录是否存在，不存在则创建
    if not os.path.exists(outfolder_name):
      os.makedirs(outfolder_name)
      return True

  return False  # 目录已存在或无需创建 


# 批量写入CSV文件
# 输入参数: curr_list_of_list = [      -->二维列表
#   ['姓名', '年龄', '职业'],          # 表头行
#   ['张三', '25', '工程师'],          # 数据行1  
#   ['李四', '30', '设计师'],          # 数据行2
#   ['王五', '28', '产品经理']         # 数据行3
# ]
# 输出参数: outfile = "data/export.csv"
# 生成的内容如下：
# 姓名,年龄,职业
# 张三,25,工程师
# 李四,30,设计师
# 王五,28,产品经理
def write_list_of_list_to_csv(curr_list_of_list, outfile):

  create_folder_if_not_there(outfile)  # 确保输出目录存在
  with open(outfile, "w") as f:
    writer = csv.writer(f)
    writer.writerows(curr_list_of_list)  # 批量写入所有行


# 逐行写入csv文件
# 注意: 此函数不自动写入表头，字段结构由调用者管理
# 输入一维列表: ['张三', '25', '工程师'] (无表头)
# 输出参数: outfile = "data/export.csv"
def write_list_to_csv_line(line_list, outfile): 

  create_folder_if_not_there(outfile)  # 确保输出目录存在

  # 以追加模式打开文件，支持增量写入
  curr_file = open(outfile, 'a',) # 追加模式打开
  csvfile_1 = csv.writer(curr_file)
  csvfile_1.writerow(line_list)  # 写入单行数据
  curr_file.close()

# 读取csv，将csv转换为python的二维表格格式，支持可选的表头处理和数据清理功能
# 输入curr_file       --> csv文件路径
# 输入header          --> 是否包含表头
# 输入strip_trail     --> 是否去除数据末尾的空格
# 输出                --> 二维列表
def read_file_to_list(curr_file, header=False, strip_trail=True): 

  if not header: # 如果不需要表头，则直接读取csv文件
    analysis_list = []
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        if strip_trail: 
          row = [i.strip() for i in row]
        analysis_list += [row]
    return analysis_list
  else: # 如果需要表头，则读取csv文件，并返回表头和数据
    analysis_list = []
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        if strip_trail: 
          row = [i.strip() for i in row]
        analysis_list += [row]
    return analysis_list[0], analysis_list[1:]


# csv文件列去重提取器
# 输入curr_file       --> csv文件路径
# 输入col             --> 要提取的列索引，从0开始，默认为第一列
# 输出                --> 集合格式
def read_file_to_set(curr_file, col=0): 

  analysis_set = set()
  with open(curr_file) as f_analysis_file: 
    data_reader = csv.reader(f_analysis_file, delimiter=",")
    for count, row in enumerate(data_reader): 
      analysis_set.add(row[col])
  return analysis_set

# 统计CSV文件中某一列的唯一值数量
# 输入curr_file       --> csv文件路径
# 输出                --> 唯一值数量
def get_row_len(curr_file): 

  try: 
    analysis_set = set()
    with open(curr_file) as f_analysis_file: 
      data_reader = csv.reader(f_analysis_file, delimiter=",")
      for count, row in enumerate(data_reader): 
        analysis_set.add(row[0])
    return len(analysis_set)
  except: 
    return False

# 检查文件是否存在
# 输入curr_file       --> 文件路径
# 输出bool            --> 是否存在
def check_if_file_exists(curr_file): 

  try: 
    with open(curr_file) as f_analysis_file: pass
    return True
  except: 
    return False

# 获取目录中指定后缀的文件
# 输入path_to_dir     --> 目录路径
# 输入suffix          --> 文件后缀
# 输出                --> 过滤指定后缀的文件列表
def find_filenames(path_to_dir, suffix=".csv"):

  filenames = listdir(path_to_dir)    # 获取目录中所有文件名
  return [ path_to_dir+"/"+filename   # 过滤指定后缀的文件并返回完整路径
           for filename in filenames if filename.endswith( suffix ) ]

# 获取列表的平均值
# 输入list_of_val     --> 列表
# 输出                --> 平均值
def average(list_of_val): 

  return sum(list_of_val)/float(len(list_of_val))


# 获取列表的标准差
# 输入list_of_val     --> 列表
# 输出                --> 标准差
def std(list_of_val): 

  std = numpy.std(list_of_val)  # 使用NumPy计算标准差
  return std

# 复制文件或目录
# 输入src             --> 源文件或目录路径
# 输入dst             --> 目标路径
# 输出                --> None
def copyanything(src, dst):

  try:
    # 尝试作为目录复制（递归复制所有内容）
    shutil.copytree(src, dst)
  except OSError as exc: 
    # 如果不是目录或格式无效，则作为单个文件复制
    if exc.errno in (errno.ENOTDIR, errno.EINVAL):
      shutil.copy(src, dst)
    else: 
      raise  # 其他错误直接抛出



if __name__ == '__main__':
  pass  # 预留测试代码位置
















