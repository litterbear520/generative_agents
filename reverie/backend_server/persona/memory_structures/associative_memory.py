import sys
sys.path.append('../../')

import json
import datetime

from global_methods import *

# 概念节点类，定义相关字段
class ConceptNode: 
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

  # 返回对象的SPO三元组
  def spo_summary(self): 
    return (self.subject, self.predicate, self.object)

# 联想记忆类，定义相关字段
class AssociativeMemory: 
  def __init__(self, f_saved): 
    # === 初始化空字典，用于存储节点ID到节点的映射表 ===
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

  # 将记忆数据保存到JSON文件
  def save(self, out_json): 

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

  # 添加事件节点
  def add_event(self, created, expiration, s, p, o, 
                      description, keywords, poignancy, 
                      embedding_pair, filling):

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

  # 添加思考节点
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

    # 添加关键词强度
    if f"{p} {o}" != "is idle":  
      for kw in keywords: 
        if kw in self.kw_strength_thought: 
          self.kw_strength_thought[kw] += 1
        else: 
          self.kw_strength_thought[kw] = 1

    self.embeddings[embedding_pair[0]] = embedding_pair[1]

    return node

  # 添加聊天节点
  def add_chat(self, created, expiration, s, p, o, 
                     description, keywords, poignancy, 
                     embedding_pair, filling): 

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

  # 获取最新的事件摘要
  def get_summarized_latest_events(self, retention): 

    ret_set = set()
    # 从事件序列的开头取retention个事件（最新的在前）
    for e_node in self.seq_event[:retention]: 
      ret_set.add(e_node.spo_summary())
    return ret_set

  # 获取事件序列的字符串表示
  # 返回值示例：
  # Event 1: (Isabella, is cooking, kitchen) -- Isabella is cooking in the kitchen
  # Event 2: (Isabella, is painting, art) -- Isabella is painting art
  # Event 3: (Isabella, is reading, book) -- Isabella is reading a book
  
  def get_str_seq_events(self):

    ret_str = ""
    # Event + 序号 + SPO三元组 + 详细描述
    for count, event in enumerate(self.seq_event): 
      ret_str += f'{"Event", len(self.seq_event) - count, ": ", event.spo_summary(), " -- ", event.description}\n'
    return ret_str

  # 获取思考序列的字符串表示
  # 返回值示例：
  # Thought 1: (Isabella, is thinking, art) -- Isabella is thinking about art
  # Thought 2: (Isabella, is thinking, book) -- Isabella is thinking about a book
  # Thought 3: (Isabella, is thinking, music) -- Isabella is thinking about music

  def get_str_seq_thoughts(self):

    ret_str = ""
    # Thought + 序号 + SPO三元组 + 详细描述
    # 思考通常比事件更复杂，描述更详细
    for count, event in enumerate(self.seq_thought):
      ret_str += f'{"Thought", len(self.seq_thought) - count, ": ", event.spo_summary(), " -- ", event.description}\n'
    return ret_str


  # 获取聊天序列的字符串表示
  # 返回值示例：
  # with Maria Lopez (Klaus Mueller converses with Maria Lopez)  --> with 对话对象 (描述)
  # February 13, 2023, 12:15:10                                  --> 对话时间
  # Klaus: Good morning Maria!                                   --> filling字段提取
  # Maria: Morning Klaus, the usual coffee?

  def get_str_seq_chats(self):

    ret_str = ""
    for count, event in enumerate(self.seq_chat):
      ret_str += f"with {event.object.content} ({event.description})\n"      # with 对话对象 (描述)
      ret_str += f'{event.created.strftime("%B %d, %Y, %H:%M:%S")}\n'        # 对话时间
      for row in event.filling:                                              # filling字段提取
        ret_str += f"{row[0]}: {row[1]}\n"
    return ret_str

  # s, p, o匹配关键词检索相关的思考节点
  # 输入: ("Klaus Mueller", "thinks about", "research")
  # 返回: {<ConceptNode1>, <ConceptNode2>, <ConceptNode3>}       --> 去重后的节点集合
  # 这些ConceptNode对象包含与"Klaus Mueller"、"thinks about"、"research"相关的所有思考记忆

  def retrieve_relevant_thoughts(self, s_content, p_content, o_content): 

    contents = [s_content, p_content, o_content]

    ret = []
    for i in contents: 
      if i in self.kw_to_thought: 
        ret += self.kw_to_thought[i.lower()]  # 关键词匹配（小写）

    ret = set(ret)  # 去重
    return ret

  # s,p,o匹配关键词检索相关的事件节点
  # 输入: ("Isabella", "works at", "cafe")
  # 返回: {<EventNode1>, <EventNode2>, <EventNode4>}             --> 去重后的节点集合
  # 包含与"Isabella"、"works at"、"cafe"相关的所有事件记忆节点

  def retrieve_relevant_events(self, s_content, p_content, o_content): 

    contents = [s_content, p_content, o_content]

    ret = []
    for i in contents: 
      if i in self.kw_to_event: 
        ret += self.kw_to_event[i]  # 关键词匹配

    ret = set(ret)  # 去重
    return ret


  # 输入: "Isabella Rodriguez"                                   --> 智能体姓名
  # 返回: <ChatNode对象> 或 False
  # 如果返回ChatNode，它包含：
  # - subject: "Klaus Mueller"
  # - predicate: "converses with"  
  # - object: "Isabella Rodriguez"
  # - description: "Klaus Mueller converses with Isabella Rodriguez"
  # - created: datetime(2023, 2, 13, 14, 30, 25)
  # - filling: [["Klaus", "Hello Isabella!"], ["Isabella", "Hi Klaus!"]]

  def get_last_chat(self, target_persona_name): 

    if target_persona_name.lower() in self.kw_to_chat: 
      # 返回该智能体对话列表中的第一个（最新的）
      return self.kw_to_chat[target_persona_name.lower()][0]
    else: 
      return False  # 没有找到相关对话记录



























