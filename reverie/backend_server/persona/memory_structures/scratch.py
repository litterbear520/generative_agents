"""
描述: 定义生成式智能体的短期记忆模块。
"""
import datetime
import json
import sys
sys.path.append('../../')

from global_methods import *

class Scratch: 
  def __init__(self, f_saved): 
    # 智能体超参数
    # 表示智能体可以看到周围的瓦片数量。
    # self.vision_r = 4
    self.att_bandwidth = 3                  # 智能体在每个时刻能够感知和处理的事件数量上限
    self.retention = 5                      # 保留期，例如3天、5天、10天

    # 世界信息
    # 感知的世界时间。
    self.curr_time = None                   # 当前时间，例如2023年2月13日12:00:00
    # # 智能体的当前 x,y 瓦片坐标。
    # self.curr_tile = None
    # # 感知的世界每日要求。
    # self.daily_plan_req = None
    
    # 关于智能体的基本信息。
    self.name = None                        # 姓名，例如Klaus Mueller
    self.first_name = None                  # 名，例如Klaus
    self.last_name = None                   # 姓，例如Mueller
    self.age = None                         # 年龄，例如20岁、25岁、30岁
    self.innate = None                      # 性格，例如善良的、好奇的、热情的
    self.learned = None                     # 简介，例如Klaus Mueller是一个学生，他喜欢阅读和写作
    self.currently = None                   # 当前状态，例如Klaus Mueller正在阅读一本书
    self.lifestyle = None                   # 生活方式，例如每天早上7点起床，晚上11点睡觉
    self.living_area = None                 # 居住地，例如住在The Ville:Dorm for Oak Hill College:Klaus Mueller's room

    # # 反思变量
    # self.concept_forget = 100
    # self.daily_reflection_time = 60 * 3
    # self.daily_reflection_size = 5
    # self.overlap_reflect_th = 2
    # self.kw_strg_event_reflect_th = 4
    # self.kw_strg_thought_reflect_th = 4

    # # 新的反思变量
    # self.recency_w = 1
    # self.relevance_w = 1
    # self.importance_w = 1
    # self.recency_decay = 0.99
    # self.importance_trigger_max = 150
    # self.importance_trigger_curr = self.importance_trigger_max
    # self.importance_ele_n = 0 
    # self.thought_count = 5

    # # 智能体规划
    # # <daily_req> 是智能体今天要实现的各种目标列表。
    # # 例如：['Work on her paintings for her upcoming show', 
    # #        'Take a break to watch some TV', 
    # #        'Make lunch for herself', 
    # #        'Work on her paintings some more', 
    # #        'Go to bed early']
    # # 它们必须在一天结束时更新，这就是为什么我们要跟踪它们首次生成的时间。
    # self.daily_req = []
    # # <f_daily_schedule> 表示一种长期规划形式，用于铺排人物当天的计划。
    # # 我们采用“长期规划 + 短期分解”的方法：先给出按小时的计划，随后逐步细化分解。
    # # 下面示例有三点说明：
    # # 1) 如 "sleeping" 不会再被分解（常见活动如睡眠被设定为不可分解）。
    # # 2) 某些元素会开始被分解，且随着一天进行会分解更多；被分解后仍保留原始的按小时描述。
    # # 3) 后续未分解的元素在新事件发生时可能会被替换或丢弃。
    # # 示例：[['sleeping', 360],
    # #       ['wakes up and ... (wakes up and stretches ...)', 5],
    # #       ['wakes up and starts her morning routine (out of bed )', 10],
    # #       ...
    # #       ['having lunch', 60],
    # #       ['working on her painting', 180], ...]
    # self.f_daily_schedule = []
    # # <f_daily_schedule_hourly_org> 初始时与 f_daily_schedule 相同，
    # # 但始终保留“未分解”的按小时版本。
    # # 示例：[['sleeping', 360],
    # #       ['wakes up and starts her morning routine', 120],
    # #       ['working on her painting', 240], ... ['going to bed', 60]]
    # self.f_daily_schedule_hourly_org = []
    
    # 当前动作（CURR ACTION）
    # <address> 为动作发生地点的字符串地址，形如
    # 访问时请避免使用负索引（如 [-1]），因为后缀元素在某些情况下可能不存在。
    # 例如："dolores double studio:double studio:bedroom 1:bed"         # address为动作发生地点的字符串地址，形如"{world}:{sector}:{arena}:{game_objects}"
    self.act_address = None                                            # 动作发生地点，例如在"The Ville:Dorm for Oak Hill College:Klaus Mueller's room"
    self.act_start_time = None                                         # 动作开始时间，例如2023年2月13日12:00:00
    self.act_duration = None                                           # 动作计划持续的分钟数，例如60分钟
    self.act_description = None                                        # 动作描述，例如sleeping
    # self.act_pronunciatio = None                                     # 动作表情表达，例如😴
    self.act_event = (self.name, None, None)                           # 动作事件三元组列表，例如[“Klaus Mueller”, “is”, “sleeping”]

    self.act_obj_description = None                                    # 被操作的物体发生了什么，例如being slept on
    # self.act_obj_pronunciatio = None                                 # 客体表情表达，例如🛏️
    self.act_obj_event = (self.name, None, None)                       # 被操作的物体事件三元组列表，例如[“bed”, “be”, “slept”]

    self.chatting_with = None                                          # 当前正在聊天的对象姓名字符串，例如"Dolores Murphy"
    self.chat = None                                                   # 对话历史记录，二维列表形如：[["Dolores Murphy", "Hi"], ["Maeve Jenson", "Hi"], ...]
    self.chat = None                                                   # 保存两人对话的列表（列表的列表），形如：[["Dolores Murphy", "Hi"], ["Maeve Jenson", "Hi"], ...]
    # self.chatting_with_buffer = dict()                               # 用于记录与谁在聊天的缓冲计数，例如：["Dolores Murphy"] = self.vision_r
    self.chatting_end_time = None                                      # 对话结束时间，例如2023年2月13日12:00:00

    # # <path_set> 表示是否已计算执行当前动作的移动路径；路径保存在
    # # scratch.planned_path 中。
    # self.act_path_set = False
    # # <planned_path> 为路径上的 (x, y) 瓦片坐标元组列表，不包含当前所在瓦片，
    # # 但包含目的地瓦片。例如：[(50, 10), (49, 10), (48, 10), ...]
    # self.planned_path = []

    # 检查并加载记忆文件
    if check_if_file_exists(f_saved): 
      # If we have a bootstrap file, load that here. 
      scratch_load = json.load(open(f_saved))

      self.vision_r = scratch_load["vision_r"]
      self.att_bandwidth = scratch_load["att_bandwidth"]
      self.retention = scratch_load["retention"]

      if scratch_load["curr_time"]: 
        self.curr_time = datetime.datetime.strptime(scratch_load["curr_time"],  # "December 25, 2023, 14:30:00" ---> datetime(2023, 12, 25, 14, 30, 0)
                                                  "%B %d, %Y, %H:%M:%S")
      else: 
        self.curr_time = None
      self.curr_tile = scratch_load["curr_tile"]
      self.daily_plan_req = scratch_load["daily_plan_req"]

      self.name = scratch_load["name"]
      self.first_name = scratch_load["first_name"]
      self.last_name = scratch_load["last_name"]
      self.age = scratch_load["age"]
      self.innate = scratch_load["innate"]
      self.learned = scratch_load["learned"]
      self.currently = scratch_load["currently"]
      self.lifestyle = scratch_load["lifestyle"]
      self.living_area = scratch_load["living_area"]

      self.concept_forget = scratch_load["concept_forget"]
      self.daily_reflection_time = scratch_load["daily_reflection_time"]
      self.daily_reflection_size = scratch_load["daily_reflection_size"]
      self.overlap_reflect_th = scratch_load["overlap_reflect_th"]
      self.kw_strg_event_reflect_th = scratch_load["kw_strg_event_reflect_th"]
      self.kw_strg_thought_reflect_th = scratch_load["kw_strg_thought_reflect_th"]

      self.recency_w = scratch_load["recency_w"]
      self.relevance_w = scratch_load["relevance_w"]
      self.importance_w = scratch_load["importance_w"]
      self.recency_decay = scratch_load["recency_decay"]
      self.importance_trigger_max = scratch_load["importance_trigger_max"]
      self.importance_trigger_curr = scratch_load["importance_trigger_curr"]
      self.importance_ele_n = scratch_load["importance_ele_n"]
      self.thought_count = scratch_load["thought_count"]

      self.daily_req = scratch_load["daily_req"]
      self.f_daily_schedule = scratch_load["f_daily_schedule"]
      self.f_daily_schedule_hourly_org = scratch_load["f_daily_schedule_hourly_org"]

      self.act_address = scratch_load["act_address"]
      if scratch_load["act_start_time"]: 
        self.act_start_time = datetime.datetime.strptime(
                                              scratch_load["act_start_time"],
                                              "%B %d, %Y, %H:%M:%S")
      else: 
        self.curr_time = None
      self.act_duration = scratch_load["act_duration"]
      self.act_description = scratch_load["act_description"]
      self.act_pronunciatio = scratch_load["act_pronunciatio"]
      self.act_event = tuple(scratch_load["act_event"])

      self.act_obj_description = scratch_load["act_obj_description"]
      self.act_obj_pronunciatio = scratch_load["act_obj_pronunciatio"]
      self.act_obj_event = tuple(scratch_load["act_obj_event"])

      self.chatting_with = scratch_load["chatting_with"]
      self.chat = scratch_load["chat"]
      self.chatting_with_buffer = scratch_load["chatting_with_buffer"]
      if scratch_load["chatting_end_time"]: 
        self.chatting_end_time = datetime.datetime.strptime(
                                            scratch_load["chatting_end_time"],
                                            "%B %d, %Y, %H:%M:%S")
      else:
        self.chatting_end_time = None

      self.act_path_set = scratch_load["act_path_set"]
      self.planned_path = scratch_load["planned_path"]


  # 保存智能体短期记忆
  def save(self, out_json):
    scratch = dict() 
    scratch["vision_r"] = self.vision_r
    scratch["att_bandwidth"] = self.att_bandwidth
    scratch["retention"] = self.retention

    scratch["curr_time"] = self.curr_time.strftime("%B %d, %Y, %H:%M:%S")
    scratch["curr_tile"] = self.curr_tile
    scratch["daily_plan_req"] = self.daily_plan_req

    scratch["name"] = self.name
    scratch["first_name"] = self.first_name
    scratch["last_name"] = self.last_name
    scratch["age"] = self.age
    scratch["innate"] = self.innate
    scratch["learned"] = self.learned
    scratch["currently"] = self.currently
    scratch["lifestyle"] = self.lifestyle
    scratch["living_area"] = self.living_area

    scratch["concept_forget"] = self.concept_forget
    scratch["daily_reflection_time"] = self.daily_reflection_time
    scratch["daily_reflection_size"] = self.daily_reflection_size
    scratch["overlap_reflect_th"] = self.overlap_reflect_th
    scratch["kw_strg_event_reflect_th"] = self.kw_strg_event_reflect_th
    scratch["kw_strg_thought_reflect_th"] = self.kw_strg_thought_reflect_th

    scratch["recency_w"] = self.recency_w
    scratch["relevance_w"] = self.relevance_w
    scratch["importance_w"] = self.importance_w
    scratch["recency_decay"] = self.recency_decay
    scratch["importance_trigger_max"] = self.importance_trigger_max
    scratch["importance_trigger_curr"] = self.importance_trigger_curr
    scratch["importance_ele_n"] = self.importance_ele_n
    scratch["thought_count"] = self.thought_count

    scratch["daily_req"] = self.daily_req
    scratch["f_daily_schedule"] = self.f_daily_schedule
    scratch["f_daily_schedule_hourly_org"] = self.f_daily_schedule_hourly_org

    scratch["act_address"] = self.act_address
    scratch["act_start_time"] = (self.act_start_time
                                     .strftime("%B %d, %Y, %H:%M:%S"))
    scratch["act_duration"] = self.act_duration
    scratch["act_description"] = self.act_description
    scratch["act_pronunciatio"] = self.act_pronunciatio
    scratch["act_event"] = self.act_event

    scratch["act_obj_description"] = self.act_obj_description
    scratch["act_obj_pronunciatio"] = self.act_obj_pronunciatio
    scratch["act_obj_event"] = self.act_obj_event

    scratch["chatting_with"] = self.chatting_with
    scratch["chat"] = self.chat
    scratch["chatting_with_buffer"] = self.chatting_with_buffer
    if self.chatting_end_time: 
      scratch["chatting_end_time"] = (self.chatting_end_time
                                        .strftime("%B %d, %Y, %H:%M:%S"))
    else: 
      scratch["chatting_end_time"] = None

    scratch["act_path_set"] = self.act_path_set
    scratch["planned_path"] = self.planned_path

    with open(out_json, "w") as outfile:
      json.dump(scratch, outfile, indent=2) 


  # def get_f_daily_schedule_index(self, advance=0):
    # """
    # 获取 self.f_daily_schedule 的当前索引。

    # 回忆一下，self.f_daily_schedule 存储到目前为止的分解动作序列，
    # 以及今天剩余时间的未来动作的每小时序列。鉴于 self.f_daily_schedule 
    # 是一个列表的列表，其中内部列表由 [任务, 持续时间] 组成，我们继续
    # 累加持续时间，直到达到 "if elapsed > today_min_elapsed" 条件。
    # 我们停止的索引就是我们将返回的索引。

    # 输入
    #   advance: 我们想要查看未来的分钟数的整数值。这允许我们获得
    #            未来时间框架的索引。
    # 输出 
    #   f_daily_schedule 当前索引的整数值。
    # """
    # # 我们首先计算今天已经过去的分钟数。
    # today_min_elapsed = 0
    # today_min_elapsed += self.curr_time.hour * 60
    # today_min_elapsed += self.curr_time.minute
    # today_min_elapsed += advance

    # x = 0
    # for task, duration in self.f_daily_schedule: 
    #   x += duration
    # x = 0
    # for task, duration in self.f_daily_schedule_hourly_org: 
    #   x += duration

    # # 然后我们基于此计算当前索引。 
    # curr_index = 0
    # elapsed = 0
    # for task, duration in self.f_daily_schedule: 
    #   elapsed += duration
    #   if elapsed > today_min_elapsed: 
    #     return curr_index
    #   curr_index += 1

    # return curr_index


  # def get_f_daily_schedule_hourly_org_index(self, advance=0):
    # """
    # 获取 self.f_daily_schedule_hourly_org 的当前索引。
    # 逻辑与 get_f_daily_schedule_index 基本相同。

    # 参数:
    #   advance (int): 想要向前查看的分钟数，用于获取未来时间片的索引。
    # 返回:
    #   int: f_daily_schedule_hourly_org 当前索引。
    # """
    # # 首先计算今天已经过去的分钟数。
    # today_min_elapsed = 0
    # today_min_elapsed += self.curr_time.hour * 60
    # today_min_elapsed += self.curr_time.minute
    # today_min_elapsed += advance
    # # 然后基于此计算当前索引。
    # curr_index = 0
    # elapsed = 0
    # for task, duration in self.f_daily_schedule_hourly_org: 
    #   elapsed += duration
    #   if elapsed > today_min_elapsed: 
    #     return curr_index
    #   curr_index += 1
    # return curr_index

  # 获取智能体基本信息，以字符串形式
  def get_str_iss(self): 

    commonset = ""
    commonset += f"Name: {self.name}\n"                                    # 姓名
    commonset += f"Age: {self.age}\n"                                      # 年龄
    commonset += f"Innate traits: {self.innate}\n"                         # 天性特质
    commonset += f"Learned traits: {self.learned}\n"                       # 学习特质
    commonset += f"Currently: {self.currently}\n"                          # 目前状态
    commonset += f"Lifestyle: {self.lifestyle}\n"                          # 生活方式
    # commonset += f"Daily plan requirement: {self.daily_plan_req}\n" 
    commonset += f"Current Date: {self.curr_time.strftime('%A %B %d')}\n"  # 当前日期
    return commonset                                                       # 返回字符串
    #例如：Name: Klaus Mueller\nAge: 22\nInnate traits: friendly, outgoing, hospitable\nLearned traits: Klaus Mueller is a student at Oak Hill College who loves to make friends. He is always looking for ways to make new friends and to be a good friend.\nCurrently: Klaus Mueller is planning on having a party at his dorm on February 14th, 2023 at 5pm. He is gathering party material, and is telling everyone to join the party at his dorm on February 14th, 2023, from 5pm to 7pm.\nLifestyle: Klaus Mueller goes to bed around 11pm, awakes up around 6am.\nCurrent Date: Tuesday September 3rd\n

  # 获取智能体姓名
  def get_str_name(self): 
    return self.name


  # 获取智能体名字
  def get_str_firstname(self): 
    return self.first_name


  # 获取智能体姓氏
  def get_str_lastname(self): 
    return self.last_name


  # 获取智能体年龄
  def get_str_age(self): 
    return str(self.age)


  # 获取智能体天性特质
  def get_str_innate(self): 
    return self.innate


  # 获取智能体学习特质
  def get_str_learned(self): 
    return self.learned

  
  # 获取智能体目前状态
  def get_str_currently(self): 
    return self.currently


  # 获取智能体生活方式
  def get_str_lifestyle(self): 
    return self.lifestyle


  # # 获取智能体每日计划需求
  # def get_str_daily_plan_req(self): 
  #   return self.daily_plan_req


  # 获取智能体当前日期
  def get_str_curr_date_str(self): 
    return self.curr_time.strftime("%A %B %d")


  # 获取当前事件的三元组列表
  def get_curr_event(self):
    if not self.act_address:                    # 如果行动地点为空
      return (self.name, None, None)            # 返回智能体姓名、none、none
    else: 
      return self.act_event                     # 返回行动事件三元组列表，
                                                # 例如[“Klaus Mueller”, “is”, “sleeping”]

  # 获取当前时间的三元组，但添加了行动描述
  def get_curr_event_and_desc(self): 
    if not self.act_address: 
      return (self.name, None, None, None)
    else: 
      return (self.act_event[0], 
              self.act_event[1], 
              self.act_event[2],
              self.act_description)


  # 获取客体事件的三元组列表，并添加了客体描述
  def get_curr_obj_event_and_desc(self): 
    if not self.act_address: 
      return ("", None, None, None)
    else: 
      return (self.act_address, 
              self.act_obj_event[1], 
              self.act_obj_event[2],
              self.act_obj_description)


  # 添加新行动和相关信息
  def add_new_action(self, 
                     action_address,              # 行动地址，例如"The Ville:Hobbs Cafe:cafe:counter"
                     action_duration,             # 行动持续时间（分钟）
                     action_description,          # 行动描述，例如"serving customers"
                    #  action_pronunciatio,       # 行动表情符号，例如"☕"
                     action_event,                # 行动事件三元组，例如["Isabella", "serve", "customers"]
                     chatting_with,               # 正在聊天的对象姓名
                     chat,                        # 聊天记录列表
                    #  chatting_with_buffer,        # 聊天缓冲区字典
                     chatting_end_time,           # 聊天结束时间
                     act_obj_description,         # 被操作对象的描述
                     # act_obj_pronunciatio,      # 被操作对象的表情符号
                     act_obj_event,               # 被操作对象的事件三元组
                     act_start_time=None):        # 行动开始时间（可选）
    self.act_address = action_address              # 设置行动地址
    self.act_duration = action_duration            # 设置行动持续时间
    self.act_description = action_description      # 设置行动描述
    # self.act_pronunciatio = action_pronunciatio    # 设置行动表情
    self.act_event = action_event                  # 设置行动事件三元组
    self.chatting_with = chatting_with             # 设置聊天对象
    self.chat = chat                               # 设置聊天记录
    # if chatting_with_buffer:                       # 如果有聊天缓冲区
    #   self.chatting_with_buffer.update(chatting_with_buffer)  # 更新聊天缓冲区
    self.chatting_end_time = chatting_end_time     # 设置聊天结束时间
    self.act_obj_description = act_obj_description      # 设置被操作对象描述
    # self.act_obj_pronunciatio = act_obj_pronunciatio   # 设置被操作对象表情
    self.act_obj_event = act_obj_event                  # 设置被操作对象事件三元组
    self.act_start_time = self.curr_time           # 设置行动开始时间为当前时间
    self.act_path_set = False                      # 重置路径设置标志

  # 返回当前动作开始时间的字符串
  def act_time_str(self): 
    return self.act_start_time.strftime("%H:%M %p")


  # 检查当前动作是否已完成
  def act_check_finished(self): 
    if not self.act_address:                       # 如果没有行动地址
      return True                                  # 返回已完成
      
    if self.chatting_with:                         # 如果正在聊天
      end_time = self.chatting_end_time            # 结束时间为聊天结束时间
    else:                                          # 如果不是聊天
      x = self.act_start_time                      # 获取行动开始时间
      if x.second != 0:                            # 如果秒数不为0
        x = x.replace(second=0)                    # 设置秒数为0
        x = (x + datetime.timedelta(minutes=1))    # 向上取整到下一分钟
      end_time = (x + datetime.timedelta(minutes=self.act_duration))  # 计算结束时间

    if end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S"):  # 比较结束时间和当前时间
      return True                                  # 如果相等，返回已完成
    return False                                   # 否则返回未完成


  # 以字典形式提取总结当前动作
  def act_summarize(self):
    exp = dict()                                   # 创建空字典
    exp["persona"] = self.name                     # 设置角色姓名
    exp["address"] = self.act_address              # 设置行动地址
    exp["start_datetime"] = self.act_start_time    # 设置开始时间
    exp["duration"] = self.act_duration            # 设置持续时间
    exp["description"] = self.act_description      # 设置行动描述
    exp["pronunciatio"] = self.act_pronunciatio    # 设置表情符号
    return exp                                     # 返回字典


  # 返回当前动作的可读字符串摘要
  def act_summary_str(self):
    start_datetime_str = self.act_start_time.strftime("%A %B %d -- %H:%M %p")  # 格式化开始时间
    ret = f"[{start_datetime_str}]\n"              # 添加时间标题
    ret += f"Activity: {self.name} is {self.act_description}\n"  # 添加活动描述
    ret += f"Address: {self.act_address}\n"        # 添加地址
    ret += f"Duration in minutes (e.g., x min): {str(self.act_duration)} min\n"  # 添加持续时间
    return ret                                     # 返回格式化字符串


  # 获取每日计划摘要字符串
  # def get_str_daily_schedule_summary(self): 
    # ret = ""                                       # 初始化返回字符串
    # curr_min_sum = 0                               # 初始化累计分钟数
    # for row in self.f_daily_schedule:              # 遍历每日计划
    #   curr_min_sum += row[1]                       # 累加分钟数
    #   hour = int(curr_min_sum/60)                  # 计算小时
    #   minute = curr_min_sum%60                     # 计算分钟
    #   ret += f"{hour:02}:{minute:02} || {row[0]}\n"  # 格式化添加到结果
    # return ret                                     # 返回摘要字符串


  # 获取每日计划原始版本摘要字符串
  # def get_str_daily_schedule_hourly_org_summary(self): 
    # ret = ""                                       # 初始化返回字符串
    # curr_min_sum = 0                               # 初始化累计分钟数
    # for row in self.f_daily_schedule_hourly_org:   # 遍历原始每日计划
    #   curr_min_sum += row[1]                       # 累加分钟数
    #   hour = int(curr_min_sum/60)                  # 计算小时
    #   minute = curr_min_sum%60                     # 计算分钟
    #   ret += f"{hour:02}:{minute:02} || {row[0]}\n"  # 格式化添加到结果
    # return ret                                     # 返回摘要字符串




















