"""
作者: Joon Sung Park (joonspk@stanford.edu)

文件: scratch.py
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
    # <vision_r> 表示智能体可以看到周围的瓦片数量。
    self.vision_r = 4
    # <att_bandwidth> 注意力带宽
    self.att_bandwidth = 3
    # <retention> 保留期
    self.retention = 5

    # 世界信息
    # 感知的世界时间。
    self.curr_time = None
    # 智能体的当前 x,y 瓦片坐标。
    self.curr_tile = None
    # 感知的世界每日要求。
    self.daily_plan_req = None
    
    # 智能体的核心身份
    # 关于智能体的基本信息。
    self.name = None
    self.first_name = None
    self.last_name = None
    self.age = None
    # L0 永久核心特征。
    self.innate = None
    # L1 稳定特征。
    self.learned = None
    # L2 外部实现。
    self.currently = None
    self.lifestyle = None
    self.living_area = None

    # 反思变量
    self.concept_forget = 100
    self.daily_reflection_time = 60 * 3
    self.daily_reflection_size = 5
    self.overlap_reflect_th = 2
    self.kw_strg_event_reflect_th = 4
    self.kw_strg_thought_reflect_th = 4

    # 新的反思变量
    self.recency_w = 1
    self.relevance_w = 1
    self.importance_w = 1
    self.recency_decay = 0.99
    self.importance_trigger_max = 150
    self.importance_trigger_curr = self.importance_trigger_max
    self.importance_ele_n = 0 
    self.thought_count = 5

    # 智能体规划
    # <daily_req> 是智能体今天要实现的各种目标列表。
    # 例如：['Work on her paintings for her upcoming show', 
    #        'Take a break to watch some TV', 
    #        'Make lunch for herself', 
    #        'Work on her paintings some more', 
    #        'Go to bed early']
    # 它们必须在一天结束时更新，这就是为什么我们要跟踪它们首次生成的时间。
    self.daily_req = []
    # <f_daily_schedule> 表示一种长期规划形式，用于铺排人物当天的计划。
    # 我们采用“长期规划 + 短期分解”的方法：先给出按小时的计划，随后逐步细化分解。
    # 下面示例有三点说明：
    # 1) 如 "sleeping" 不会再被分解（常见活动如睡眠被设定为不可分解）。
    # 2) 某些元素会开始被分解，且随着一天进行会分解更多；被分解后仍保留原始的按小时描述。
    # 3) 后续未分解的元素在新事件发生时可能会被替换或丢弃。
    # 示例：[['sleeping', 360],
    #       ['wakes up and ... (wakes up and stretches ...)', 5],
    #       ['wakes up and starts her morning routine (out of bed )', 10],
    #       ...
    #       ['having lunch', 60],
    #       ['working on her painting', 180], ...]
    self.f_daily_schedule = []
    # <f_daily_schedule_hourly_org> 初始时与 f_daily_schedule 相同，
    # 但始终保留“未分解”的按小时版本。
    # 示例：[['sleeping', 360],
    #       ['wakes up and starts her morning routine', 120],
    #       ['working on her painting', 240], ... ['going to bed', 60]]
    self.f_daily_schedule_hourly_org = []
    
    # 当前动作（CURR ACTION）
    # <address> 为动作发生地点的字符串地址，形如
    # "{world}:{sector}:{arena}:{game_objects}"。
    # 访问时请避免使用负索引（如 [-1]），因为后缀元素在某些情况下可能不存在。
    # 例如："dolores double studio:double studio:bedroom 1:bed"
    self.act_address = None
    # <start_time> 为动作开始的 datetime 时间。
    self.act_start_time = None
    # <duration> 为动作计划持续的分钟数（整数）。
    self.act_duration = None
    # <description> 为动作的字符串描述。
    self.act_description = None
    # <pronunciatio> 为对 self.description 的表达，目前用表情符号实现。
    self.act_pronunciatio = None
    # <event_form> 表示人物当前所处的事件三元组（SPO）。
    self.act_event = (self.name, None, None)

    # <obj_description> 为“客体动作”的字符串描述。
    self.act_obj_description = None
    # <obj_pronunciatio> 为“客体动作”的表达，目前用表情符号实现。
    self.act_obj_pronunciatio = None
    # <obj_event_form> 表示动作客体当前所处的事件三元组（SPO）。
    self.act_obj_event = (self.name, None, None)

    # <chatting_with> 为当前正在聊天的对象姓名字符串；若无则为 None。
    self.chatting_with = None
    # <chat> 保存两人对话的列表（列表的列表），形如：
    # [["Dolores Murphy", "Hi"], ["Maeve Jenson", "Hi"], ...]
    self.chat = None
    # <chatting_with_buffer> 用于记录与谁在聊天的缓冲计数，例如：
    # ["Dolores Murphy"] = self.vision_r
    self.chatting_with_buffer = dict()
    self.chatting_end_time = None

    # <path_set> 表示是否已计算执行当前动作的移动路径；路径保存在
    # scratch.planned_path 中。
    self.act_path_set = False
    # <planned_path> 为路径上的 (x, y) 瓦片坐标元组列表，不包含当前所在瓦片，
    # 但包含目的地瓦片。例如：[(50, 10), (49, 10), (48, 10), ...]
    self.planned_path = []

    if check_if_file_exists(f_saved): 
      # If we have a bootstrap file, load that here. 
      scratch_load = json.load(open(f_saved))

      self.vision_r = scratch_load["vision_r"]
      self.att_bandwidth = scratch_load["att_bandwidth"]
      self.retention = scratch_load["retention"]

      if scratch_load["curr_time"]: 
        self.curr_time = datetime.datetime.strptime(scratch_load["curr_time"],
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


  def save(self, out_json):
    """
    保存智能体的短期记忆。

    输入: 
      out_json: 我们将保存智能体状态的文件。
    输出: 
      None
    """
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


  def get_f_daily_schedule_index(self, advance=0):
    """
    获取 self.f_daily_schedule 的当前索引。

    回忆一下，self.f_daily_schedule 存储到目前为止的分解动作序列，
    以及今天剩余时间的未来动作的每小时序列。鉴于 self.f_daily_schedule 
    是一个列表的列表，其中内部列表由 [任务, 持续时间] 组成，我们继续
    累加持续时间，直到达到 "if elapsed > today_min_elapsed" 条件。
    我们停止的索引就是我们将返回的索引。

    输入
      advance: 我们想要查看未来的分钟数的整数值。这允许我们获得
               未来时间框架的索引。
    输出 
      f_daily_schedule 当前索引的整数值。
    """
    # 我们首先计算今天已经过去的分钟数。
    today_min_elapsed = 0
    today_min_elapsed += self.curr_time.hour * 60
    today_min_elapsed += self.curr_time.minute
    today_min_elapsed += advance

    x = 0
    for task, duration in self.f_daily_schedule: 
      x += duration
    x = 0
    for task, duration in self.f_daily_schedule_hourly_org: 
      x += duration

    # 然后我们基于此计算当前索引。 
    curr_index = 0
    elapsed = 0
    for task, duration in self.f_daily_schedule: 
      elapsed += duration
      if elapsed > today_min_elapsed: 
        return curr_index
      curr_index += 1

    return curr_index


  def get_f_daily_schedule_hourly_org_index(self, advance=0):
    """
    获取 self.f_daily_schedule_hourly_org 的当前索引。
    逻辑与 get_f_daily_schedule_index 基本相同。

    参数:
      advance (int): 想要向前查看的分钟数，用于获取未来时间片的索引。
    返回:
      int: f_daily_schedule_hourly_org 当前索引。
    """
    # 首先计算今天已经过去的分钟数。
    today_min_elapsed = 0
    today_min_elapsed += self.curr_time.hour * 60
    today_min_elapsed += self.curr_time.minute
    today_min_elapsed += advance
    # 然后基于此计算当前索引。
    curr_index = 0
    elapsed = 0
    for task, duration in self.f_daily_schedule_hourly_org: 
      elapsed += duration
      if elapsed > today_min_elapsed: 
        return curr_index
      curr_index += 1
    return curr_index


  def get_str_iss(self): 
    """
    ISS 代表"身份稳定集"。这描述了此智能体的通用集合摘要 -- 基本上是
    智能体的最基本描述，几乎在所有需要调用智能体的提示中都会用到。

    输入
      None
    输出
      智能体身份稳定集摘要的字符串形式。
    示例字符串输出
      "Name: Dolores Heitmiller
       Age: 28
       Innate traits: hard-edged, independent, loyal
       Learned traits: Dolores is a painter who wants live quietly and paint 
         while enjoying her everyday life.
       Currently: Dolores is preparing for her first solo show. She mostly 
         works from home.
       Lifestyle: Dolores goes to bed around 11pm, sleeps for 7 hours, eats 
         dinner around 6pm.
       Daily plan requirement: Dolores is planning to stay at home all day and 
         never go out."
    """
    commonset = ""
    commonset += f"Name: {self.name}\n"
    commonset += f"Age: {self.age}\n"
    commonset += f"Innate traits: {self.innate}\n"
    commonset += f"Learned traits: {self.learned}\n"
    commonset += f"Currently: {self.currently}\n"
    commonset += f"Lifestyle: {self.lifestyle}\n"
    commonset += f"Daily plan requirement: {self.daily_plan_req}\n"
    commonset += f"Current Date: {self.curr_time.strftime('%A %B %d')}\n"
    return commonset


  def get_str_name(self): 
    return self.name


  def get_str_firstname(self): 
    return self.first_name


  def get_str_lastname(self): 
    return self.last_name


  def get_str_age(self): 
    return str(self.age)


  def get_str_innate(self): 
    return self.innate


  def get_str_learned(self): 
    return self.learned


  def get_str_currently(self): 
    return self.currently


  def get_str_lifestyle(self): 
    return self.lifestyle


  def get_str_daily_plan_req(self): 
    return self.daily_plan_req


  def get_str_curr_date_str(self): 
    return self.curr_time.strftime("%A %B %d")


  def get_curr_event(self):
    if not self.act_address: 
      return (self.name, None, None)
    else: 
      return self.act_event


  def get_curr_event_and_desc(self): 
    if not self.act_address: 
      return (self.name, None, None, None)
    else: 
      return (self.act_event[0], 
              self.act_event[1], 
              self.act_event[2],
              self.act_description)


  def get_curr_obj_event_and_desc(self): 
    if not self.act_address: 
      return ("", None, None, None)
    else: 
      return (self.act_address, 
              self.act_obj_event[1], 
              self.act_obj_event[2],
              self.act_obj_description)


  def add_new_action(self, 
                     action_address, 
                     action_duration,
                     action_description,
                     action_pronunciatio, 
                     action_event,
                     chatting_with, 
                     chat, 
                     chatting_with_buffer,
                     chatting_end_time,
                     act_obj_description, 
                     act_obj_pronunciatio, 
                     act_obj_event, 
                     act_start_time=None): 
    self.act_address = action_address
    self.act_duration = action_duration
    self.act_description = action_description
    self.act_pronunciatio = action_pronunciatio
    self.act_event = action_event

    self.chatting_with = chatting_with
    self.chat = chat 
    if chatting_with_buffer: 
      self.chatting_with_buffer.update(chatting_with_buffer)
    self.chatting_end_time = chatting_end_time

    self.act_obj_description = act_obj_description
    self.act_obj_pronunciatio = act_obj_pronunciatio
    self.act_obj_event = act_obj_event
    
    self.act_start_time = self.curr_time
    
    self.act_path_set = False


  def act_time_str(self): 
    """
    返回当前动作开始时间的字符串。

    参数:
      None
    返回:
      str: 当前时间的字符串表示。
    示例:
      "14:05 P.M."
    """
    return self.act_start_time.strftime("%H:%M %p")


  def act_check_finished(self): 
    """
    检查当前动作是否已完成。

    参数:
      None
    返回:
      bool: True 表示已结束；False 表示仍在进行中。
    说明:
      若当前时间等于（聊天结束时间 或 开始时间对齐到整分后 + 持续时长）则判定结束。
    """
    if not self.act_address: 
      return True
      
    if self.chatting_with: 
      end_time = self.chatting_end_time
    else: 
      x = self.act_start_time
      if x.second != 0: 
        x = x.replace(second=0)
        x = (x + datetime.timedelta(minutes=1))
      end_time = (x + datetime.timedelta(minutes=self.act_duration))

    if end_time.strftime("%H:%M:%S") == self.curr_time.strftime("%H:%M:%S"): 
      return True
    return False


  def act_summarize(self):
    """
    以字典形式总结当前动作（便于程序使用）。

    参数:
      None
    返回:
      dict: 对当前动作的结构化摘要。
    """
    exp = dict()
    exp["persona"] = self.name
    exp["address"] = self.act_address
    exp["start_datetime"] = self.act_start_time
    exp["duration"] = self.act_duration
    exp["description"] = self.act_description
    exp["pronunciatio"] = self.act_pronunciatio
    return exp


  def act_summary_str(self):
    """
    返回当前动作的可读字符串摘要（面向人类阅读）。

    参数:
      None
    返回:
      str: 当前动作的简要描述字符串。
    """
    start_datetime_str = self.act_start_time.strftime("%A %B %d -- %H:%M %p")
    ret = f"[{start_datetime_str}]\n"
    ret += f"Activity: {self.name} is {self.act_description}\n"
    ret += f"Address: {self.act_address}\n"
    ret += f"Duration in minutes (e.g., x min): {str(self.act_duration)} min\n"
    return ret


  def get_str_daily_schedule_summary(self): 
    ret = ""
    curr_min_sum = 0
    for row in self.f_daily_schedule: 
      curr_min_sum += row[1]
      hour = int(curr_min_sum/60)
      minute = curr_min_sum%60
      ret += f"{hour:02}:{minute:02} || {row[0]}\n"
    return ret


  def get_str_daily_schedule_hourly_org_summary(self): 
    ret = ""
    curr_min_sum = 0
    for row in self.f_daily_schedule_hourly_org: 
      curr_min_sum += row[1]
      hour = int(curr_min_sum/60)
      minute = curr_min_sum%60
      ret += f"{hour:02}:{minute:02} || {row[0]}\n"
    return ret




















