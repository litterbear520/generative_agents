"""
作者: Joon Sung Park (joonspk@stanford.edu)

文件: associative_memory.py
描述: 定义生成式智能体的核心长期记忆模块。

注意 (2023年5月1日) -- 这个类是生成式智能体论文中的记忆流(Memory Stream)模块。

=== 联想记忆系统架构说明 ===

1. 数据结构层次：
   ConceptNode (概念节点) - 记忆的基本单元
   ├── 标识信息: node_id, type, depth
   ├── 时间属性: created, expiration, last_accessed  
   ├── SPO结构: subject-predicate-object 三元组
   └── 元数据: description, keywords, poignancy, embedding

2. 记忆类型分类：
   - Event (事件): depth=0, 直接观察的行为和状态变化
   - Thought (思考): depth≥1, 基于事件的反思和抽象推理
   - Chat (对话): depth=0, 与其他智能体的交流记录

3. 索引机制：
   - ID映射: id_to_node - 通过唯一ID快速定位节点
   - 时序列表: seq_event/thought/chat - 按时间排序的记忆序列
   - 关键词索引: kw_to_* - 支持基于关键词的快速检索
   - 强度统计: kw_strength_* - 跟踪关键词的重要性权重
   - 语义嵌入: embeddings - 支持向量相似度检索

4. 核心操作：
   - 添加记忆: add_event/thought/chat - 创建新记忆并更新索引
   - 检索记忆: retrieve_relevant_* - 基于内容关联检索
   - 持久化: save/load - JSON格式的序列化存储

这个系统实现了人类记忆的关键特征：时序性、关联性、重要性权重、遗忘机制。
"""
import sys
sys.path.append('../../')

import json
import datetime

from global_methods import *


class ConceptNode: 
  """
  概念节点类 - 记忆流中的基本单元
  
  每个 ConceptNode 代表智能体记忆中的一个概念，可以是：
  - 事件(event): 观察到的行为或状态变化，深度=0
  - 思考(thought): 基于事件的反思和抽象，深度≥1  
  - 对话(chat): 与其他智能体的交流记录，深度=0
  """
  def __init__(self,
               node_id, node_count, type_count, node_type, depth,
               created, expiration, 
               s, p, o, 
               description, embedding_key, poignancy, keywords, filling): 
    # === 节点标识信息 ===
    self.node_id = node_id           # 唯一ID: "node_1", "node_2"...
    self.node_count = node_count     # 全局节点计数器
    self.type_count = type_count     # 同类型节点计数器
    self.type = node_type           # 节点类型: "event"/"thought"/"chat"
    self.depth = depth              # 抽象层级: 0=原始观察, 1+=反思层级

    # === 时间属性 ===
    self.created = created          # 创建时间(datetime对象)
    self.expiration = expiration    # 过期时间(可选，用于临时记忆)
    self.last_accessed = self.created  # 最后访问时间(用于时近性计算)

    # === SPO三元组结构 (主语-谓语-宾语) ===
    self.subject = s                # 主语: 谁/什么
    self.predicate = p              # 谓语: 做什么/是什么状态
    self.object = o                 # 宾语: 对什么/在哪里

    # === 内容和元数据 ===
    self.description = description   # 人类可读的描述文本
    self.embedding_key = embedding_key  # 向量嵌入的键名
    self.poignancy = poignancy      # 重要性/情感强度评分(1-10)
    self.keywords = keywords        # 关键词集合(用于快速检索)
    self.filling = filling          # 填充信息(用于思考节点的支撑证据)


  def spo_summary(self): 
    """
    返回SPO三元组摘要
    
    返回:
        tuple: (主语, 谓语, 宾语) 的元组形式
    
    示例:
        ("Isabella Rodriguez", "is", "sleeping") 
        ("咖啡馆", "位于", "小镇中心")
    """
    return (self.subject, self.predicate, self.object)


class AssociativeMemory: 
  """
  联想记忆类 - 智能体的长期记忆系统
  
  这是AI小镇项目的核心记忆模块，实现了论文中的Memory Stream概念。
  它维护智能体的所有长期记忆，并提供高效的检索机制。
  
  主要功能:
  1. 存储三种类型的记忆: 事件、思考、对话
  2. 提供多维度索引: ID映射、时序列表、关键词索引
  3. 支持语义检索: 向量嵌入和相似度计算
  4. 统计关键词强度: 用于重要性评估
  """
  def __init__(self, f_saved): 
    # === 核心数据结构 ===
    self.id_to_node = dict()        # ID到节点的映射表 {"node_1": ConceptNode, ...}

    # === 按类型分类的时序列表 (最新的在前) ===
    self.seq_event = []             # 事件序列 [newest_event, ..., oldest_event]
    self.seq_thought = []           # 思考序列 [newest_thought, ..., oldest_thought]  
    self.seq_chat = []              # 对话序列 [newest_chat, ..., oldest_chat]

    # === 关键词倒排索引 (用于快速检索) ===
    self.kw_to_event = dict()       # 关键词->事件节点列表 {"sleep": [node1, node2]}
    self.kw_to_thought = dict()     # 关键词->思考节点列表  
    self.kw_to_chat = dict()        # 关键词->对话节点列表

    # === 关键词统计强度 (用于重要性计算) ===
    self.kw_strength_event = dict()   # 事件中关键词出现频次 {"sleep": 5}
    self.kw_strength_thought = dict() # 思考中关键词出现频次

    # === 语义向量嵌入库 ===
    self.embeddings = json.load(open(f_saved + "/embeddings.json"))

    # === 从保存的JSON文件加载现有记忆 ===
    nodes_load = json.load(open(f_saved + "/nodes.json"))
    for count in range(len(nodes_load.keys())): 
      node_id = f"node_{str(count+1)}"
      node_details = nodes_load[node_id]

      # 提取节点基本信息
      node_count = node_details["node_count"]
      type_count = node_details["type_count"] 
      node_type = node_details["type"]
      depth = node_details["depth"]

      # 解析时间信息
      created = datetime.datetime.strptime(node_details["created"], 
                                           '%Y-%m-%d %H:%M:%S')
      expiration = None
      if node_details["expiration"]: 
        expiration = datetime.datetime.strptime(node_details["expiration"],
                                                '%Y-%m-%d %H:%M:%S')

      # 提取SPO三元组
      s = node_details["subject"]      # 主语
      p = node_details["predicate"]    # 谓语  
      o = node_details["object"]       # 宾语

      # 提取描述和元数据
      description = node_details["description"]
      embedding_pair = (node_details["embedding_key"], 
                        self.embeddings[node_details["embedding_key"]])
      poignancy = node_details["poignancy"]    # 重要性评分
      keywords = set(node_details["keywords"])  # 关键词集合
      filling = node_details["filling"]        # 填充信息
      
      # 根据节点类型调用相应的添加方法，重建内存中的索引结构
      if node_type == "event": 
        self.add_event(created, expiration, s, p, o, 
                   description, keywords, poignancy, embedding_pair, filling)
      elif node_type == "chat": 
        self.add_chat(created, expiration, s, p, o, 
                   description, keywords, poignancy, embedding_pair, filling)
      elif node_type == "thought": 
        self.add_thought(created, expiration, s, p, o, 
                   description, keywords, poignancy, embedding_pair, filling)

    # === 加载关键词强度统计数据 ===
    kw_strength_load = json.load(open(f_saved + "/kw_strength.json"))
    if kw_strength_load["kw_strength_event"]: 
      self.kw_strength_event = kw_strength_load["kw_strength_event"]
    if kw_strength_load["kw_strength_thought"]: 
      self.kw_strength_thought = kw_strength_load["kw_strength_thought"]

    
  def save(self, out_json): 
    """
    将记忆数据保存到JSON文件
    
    这个方法将内存中的所有记忆节点序列化为JSON格式，保存到指定目录。
    保存的文件包括:
    1. nodes.json - 所有记忆节点的详细信息
    2. kw_strength.json - 关键词强度统计
    3. embeddings.json - 向量嵌入数据
    
    参数:
        out_json (str): 输出目录路径
    """
    # === 保存所有记忆节点到 nodes.json ===
    r = dict()
    # 注意：这里倒序遍历是为了保持节点ID的顺序性
    for count in range(len(self.id_to_node.keys()), 0, -1): 
      node_id = f"node_{str(count)}" # f""实现拼接，将数字转换为字符串，并添加前缀 "node_"
      node = self.id_to_node[node_id]

      # 序列化单个节点的所有属性
      r[node_id] = dict()
      r[node_id]["node_count"] = node.node_count
      r[node_id]["type_count"] = node.type_count
      r[node_id]["type"] = node.type
      r[node_id]["depth"] = node.depth

      # 时间格式化为字符串
      r[node_id]["created"] = node.created.strftime('%Y-%m-%d %H:%M:%S')
      r[node_id]["expiration"] = None
      if node.expiration: 
        r[node_id]["expiration"] = (node.expiration
                                        .strftime('%Y-%m-%d %H:%M:%S'))

      # SPO三元组
      r[node_id]["subject"] = node.subject
      r[node_id]["predicate"] = node.predicate
      r[node_id]["object"] = node.object

      # 内容和元数据
      r[node_id]["description"] = node.description
      r[node_id]["embedding_key"] = node.embedding_key
      r[node_id]["poignancy"] = node.poignancy
      r[node_id]["keywords"] = list(node.keywords)  # 集合转为列表
      r[node_id]["filling"] = node.filling

    # 写入节点文件
    with open(out_json+"/nodes.json", "w") as outfile:
      json.dump(r, outfile)

    # === 保存关键词强度统计到 kw_strength.json ===
    r = dict()
    r["kw_strength_event"] = self.kw_strength_event
    r["kw_strength_thought"] = self.kw_strength_thought
    with open(out_json+"/kw_strength.json", "w") as outfile:
      json.dump(r, outfile)

    # === 保存向量嵌入到 embeddings.json ===
    with open(out_json+"/embeddings.json", "w") as outfile:
      json.dump(self.embeddings, outfile)


  def add_event(self, created, expiration, s, p, o, 
                      description, keywords, poignancy, 
                      embedding_pair, filling):
    """
    添加新的事件记忆节点
    
    事件是智能体直接观察到的行为或状态变化，属于原始观察记忆（depth=0）。
    
    参数:
        created (datetime): 事件发生时间
        expiration (datetime): 过期时间（可为None） 
        s (str): 主语 - 执行动作的主体
        p (str): 谓语 - 动作或状态
        o (str): 宾语 - 动作的对象或描述
        description (str): 事件的自然语言描述
        keywords (set): 关键词集合，用于检索
        poignancy (int): 重要性评分 (1-10)
        embedding_pair (tuple): (embedding_key, embedding_vector)
        filling (list): 支撑信息（通常为空）
        
    返回:
        ConceptNode: 创建的事件节点
        
    示例:
        add_event(
            created=datetime.now(),
            s="Isabella Rodriguez", 
            p="is", 
            o="sleeping",
            description="Isabella Rodriguez is sleeping"
        )
    """
    # === 设置节点标识和类型信息 ===
    node_count = len(self.id_to_node.keys()) + 1  # 全局节点计数器
    type_count = len(self.seq_event) + 1           # 事件节点计数器
    node_type = "event"
    node_id = f"node_{str(node_count)}"
    depth = 0  # 事件节点始终为原始观察层级

    # === 描述文本的清理和规范化 ===
    # 处理带括号的描述，提取关键信息
    if "(" in description: 
      description = (" ".join(description.split()[:3]) 
                     + " " 
                     +  description.split("(")[-1][:-1])

    # === 创建概念节点对象 ===
    node = ConceptNode(node_id, node_count, type_count, node_type, depth,
                       created, expiration, 
                       s, p, o, 
                       description, embedding_pair[0], 
                       poignancy, keywords, filling)

    # === 更新各种索引结构（插入到列表头部，保持时序） ===
    # 由于左闭右开，这个切片本身是空的，当对这个 “空切片” 赋值时，
    # Python 会把新元素插入到这个切片的位置，也就是开头
    self.seq_event[0:0] = [node]  # 将新事件插入到事件序列的开头
    
    # 更新关键词倒排索引（关键词转小写以统一检索）
    keywords = [i.lower() for i in keywords]
    for kw in keywords: 
      if kw in self.kw_to_event: 
        self.kw_to_event[kw][0:0] = [node]  # 插入到该关键词对应列表的开头
      else: 
        self.kw_to_event[kw] = [node]       # 创建新的关键词条目
    
    # 更新ID映射表
    self.id_to_node[node_id] = node 

    # === 更新关键词强度统计（排除idle状态） ===
    if f"{p} {o}" != "is idle":   # 过滤掉无意义的idle状态
      for kw in keywords: 
        if kw in self.kw_strength_event: 
          self.kw_strength_event[kw] += 1    # 增加现有关键词计数
        else: 
          self.kw_strength_event[kw] = 1     # 初始化新关键词计数

    # === 存储向量嵌入数据 ===
    self.embeddings[embedding_pair[0]] = embedding_pair[1]

    return node


  def add_thought(self, created, expiration, s, p, o, 
                        description, keywords, poignancy, 
                        embedding_pair, filling):
    # 设置节点 ID 和计数。
    node_count = len(self.id_to_node.keys()) + 1
    type_count = len(self.seq_thought) + 1
    node_type = "thought"
    node_id = f"node_{str(node_count)}"
    depth = 1 
    try: 
      if filling: 
        depth += max([self.id_to_node[i].depth for i in filling])
    except: 
      pass

    # 创建 <ConceptNode> 对象。
    node = ConceptNode(node_id, node_count, type_count, node_type, depth,
                       created, expiration, 
                       s, p, o, 
                       description, embedding_pair[0], poignancy, keywords, filling)

    # 创建各种字典缓存以便快速访问。
    self.seq_thought[0:0] = [node]
    keywords = [i.lower() for i in keywords]
    for kw in keywords: 
      if kw in self.kw_to_thought: 
        self.kw_to_thought[kw][0:0] = [node]
      else: 
        self.kw_to_thought[kw] = [node]
    self.id_to_node[node_id] = node 

    # Adding in the kw_strength
    if f"{p} {o}" != "is idle":  
      for kw in keywords: 
        if kw in self.kw_strength_thought: 
          self.kw_strength_thought[kw] += 1
        else: 
          self.kw_strength_thought[kw] = 1

    self.embeddings[embedding_pair[0]] = embedding_pair[1]

    return node


  def add_chat(self, created, expiration, s, p, o, 
                     description, keywords, poignancy, 
                     embedding_pair, filling): 
    """
    向关联记忆中添加一个聊天事件。

    参数:
      created (datetime): 聊天事件的创建时间。
      expiration (datetime): 聊天事件的过期时间。
      s (ConceptNode): 聊天的主语节点。
      p (ConceptNode): 聊天的谓语节点。
      o (ConceptNode): 聊天的宾语节点。
      description (str): 聊天事件的描述。
      keywords (list): 与聊天事件相关的关键词列表。
      poignancy (int): 聊天事件的深刻性/重要性。
      embedding_pair (tuple): 包含嵌入ID和嵌入向量的元组。
      filling (list): 聊天内容的详细填充信息。

    返回值:
      ConceptNode: 新创建的聊天事件节点。
    """
    # 设置节点ID和计数。
    node_count = len(self.id_to_node.keys()) + 1
    type_count = len(self.seq_chat) + 1
    node_type = "chat"
    node_id = f"node_{str(node_count)}"
    depth = 0

    # 创建 ConceptNode 对象。
    node = ConceptNode(node_id, node_count, type_count, node_type, depth,
                       created, expiration, 
                       s, p, o, 
                       description, embedding_pair[0], poignancy, keywords, filling)

    # 创建各种字典缓存以实现快速访问。
    # 将新聊天事件添加到聊天序列的开头（最近的在前面）。
    self.seq_chat[0:0] = [node]
    # 将关键词转换为小写。
    keywords = [i.lower() for i in keywords]
    for kw in keywords: 
      # 如果关键词已存在，则将新节点添加到对应关键词的聊天事件列表开头。
      if kw in self.kw_to_chat: 
        self.kw_to_chat[kw][0:0] = [node]
      # 否则，创建一个新的关键词条目。
      else: 
        self.kw_to_chat[kw] = [node]
    # 将新节点添加到ID到节点映射中。
    self.id_to_node[node_id] = node 

    # 存储嵌入向量。
    self.embeddings[embedding_pair[0]] = embedding_pair[1]
        
    return node


  def get_summarized_latest_events(self, retention): 
    """
    获取最近事件的SPO摘要集合
    
    从事件序列中提取最近的N个事件，返回它们的SPO三元组摘要。
    这个方法用于快速获取智能体的近期经历概览。
    
    参数:
        retention (int): 要检索的最近事件数量
        
    返回:
        set: SPO三元组的集合 {(subject, predicate, object), ...}
        
    示例:
        get_summarized_latest_events(5)
        返回: {("Isabella", "is", "sleeping"), ("cafe", "is", "open"), ...}
    """
    ret_set = set()
    # 从事件序列的开头取retention个事件（最新的在前）
    for e_node in self.seq_event[:retention]: 
      ret_set.add(e_node.spo_summary())
    return ret_set


  def get_str_seq_events(self):
    """
    将按时间倒序排列的事件序列转换为字符串。

    返回值:
      str: 包含事件摘要和描述的格式化字符串。
    """
    ret_str = ""
    for count, event in enumerate(self.seq_event): 
      ret_str += f'{"Event", len(self.seq_event) - count, ": ", event.spo_summary(), " -- ", event.description}\n'
    return ret_str


  def get_str_seq_thoughts(self):
    """
    将按时间倒序排列的思考序列转换为字符串。

    返回值:
      str: 包含思考摘要和描述的格式化字符串，每个思考事件占据一行。
    """
    ret_str = ""
    for count, event in enumerate(self.seq_thought):
      ret_str += f'{"Thought", len(self.seq_thought) - count, ": ", event.spo_summary(), " -- ", event.description}\n'
    return ret_str


  def get_str_seq_chats(self):
    """
    将按时间倒序排列的聊天序列转换为字符串。

    返回值:
      str: 包含聊天摘要（与谁聊天、时间、内容）的格式化字符串。
    """
    ret_str = ""
    for count, event in enumerate(self.seq_chat):
      ret_str += f"with {event.object.content} ({event.description})\n"
      ret_str += f'{event.created.strftime("%B %d, %Y, %H:%M:%S")}\n'
      for row in event.filling:
        ret_str += f"{row[0]}: {row[1]}\n"
    return ret_str


  def retrieve_relevant_thoughts(self, s_content, p_content, o_content): 
    """
    基于SPO内容检索相关的思考记忆
    
    通过关键词匹配的方式，从思考记忆中找出与给定SPO三元组相关的节点。
    这是一种简单但有效的关联检索方法。
    
    参数:
        s_content (str): 主语内容
        p_content (str): 谓语内容  
        o_content (str): 宾语内容
        
    返回:
        set: 相关思考节点的集合
        
    示例:
        retrieve_relevant_thoughts("Isabella", "painting", "art")
        返回与绘画艺术相关的所有思考记忆
    """
    contents = [s_content, p_content, o_content]

    ret = []
    for i in contents: 
      if i in self.kw_to_thought: 
        ret += self.kw_to_thought[i.lower()]  # 关键词匹配（小写）

    ret = set(ret)  # 去重
    return ret


  def retrieve_relevant_events(self, s_content, p_content, o_content): 
    """
    基于SPO内容检索相关的事件记忆
    
    通过关键词匹配的方式，从事件记忆中找出与给定SPO三元组相关的节点。
    这用于寻找智能体的相关经历和观察。
    
    参数:
        s_content (str): 主语内容
        p_content (str): 谓语内容
        o_content (str): 宾语内容
        
    返回:
        set: 相关事件节点的集合
        
    示例:
        retrieve_relevant_events("Isabella", "cooking", "kitchen")
        返回Isabella在厨房做饭的相关事件记忆
    """
    contents = [s_content, p_content, o_content]

    ret = []
    for i in contents: 
      if i in self.kw_to_event: 
        ret += self.kw_to_event[i]  # 关键词匹配

    ret = set(ret)  # 去重
    return ret


  def get_last_chat(self, target_persona_name): 
    """
    获取与指定智能体的最近一次对话记录
    
    通过智能体姓名作为关键词，从对话记忆中查找最近的交流记录。
    这用于维持对话的连续性和上下文。
    
    参数:
        target_persona_name (str): 目标智能体的姓名
        
    返回:
        ConceptNode or False: 最近的对话节点，如果没有则返回False
        
    示例:
        get_last_chat("Klaus Mueller")
        返回与Klaus的最近一次对话记忆，或False（如果从未对话）
    """
    if target_persona_name.lower() in self.kw_to_chat: 
      # 返回该智能体对话列表中的第一个（最新的）
      return self.kw_to_chat[target_persona_name.lower()][0]
    else: 
      return False  # 没有找到相关对话记录



























