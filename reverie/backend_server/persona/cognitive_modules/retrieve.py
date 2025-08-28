"""
作者: Joon Sung Park (joonspk@stanford.edu)

文件: retrieve.py
描述: 定义生成式智能体的"检索"模块。
"""
import sys
sys.path.append('../../')

from global_methods import *
from persona.prompt_template.gpt_structure import *

from numpy import dot
from numpy.linalg import norm

def retrieve(persona, perceived): 
  """
  此函数接受智能体感知到的事件作为输入，并返回智能体在规划时需要考虑作为上下文的
  相关事件和思考集合。

  输入: 
    perceived: 表示智能体周围发生的任何事件的事件 <ConceptNode> 列表。
              这里包含的内容由 att_bandwidth 和 retention 超参数控制。
  输出: 
    retrieved: 字典的字典。第一层指定一个事件，后一层指定相关的
              "curr_event"、"events" 和 "thoughts"。
  """
  # 我们分别检索事件和思考。 
  retrieved = dict()
  for event in perceived: 
    retrieved[event.description] = dict()
    retrieved[event.description]["curr_event"] = event
    
    relevant_events = persona.a_mem.retrieve_relevant_events(
                        event.subject, event.predicate, event.object)
    retrieved[event.description]["events"] = list(relevant_events)

    relevant_thoughts = persona.a_mem.retrieve_relevant_thoughts(
                          event.subject, event.predicate, event.object)
    retrieved[event.description]["thoughts"] = list(relevant_thoughts)
    
  return retrieved


def cos_sim(a, b): 
  """
  此函数计算两个输入向量 'a' 和 'b' 之间的余弦相似度。余弦相似度是内积空间中
  两个非零向量之间相似度的度量，它度量它们之间角度的余弦值。

  输入: 
    a: 1维数组对象
    b: 1维数组对象
  输出: 
    表示输入向量 'a' 和 'b' 之间余弦相似度的标量值。
  
  输入示例: 
    a = [0.3, 0.2, 0.5]
    b = [0.2, 0.2, 0.5]
  """
  return dot(a, b)/(norm(a)*norm(b))


def normalize_dict_floats(d, target_min, target_max):
  """
  This function normalizes the float values of a given dictionary 'd' between 
  a target minimum and maximum value. The normalization is done by scaling the
  values to the target range while maintaining the same relative proportions 
  between the original values.

  INPUT: 
    d: Dictionary. The input dictionary whose float values need to be 
       normalized.
    target_min: Integer or float. The minimum value to which the original 
                values should be scaled.
    target_max: Integer or float. The maximum value to which the original 
                values should be scaled.
  OUTPUT: 
    d: A new dictionary with the same keys as the input but with the float
       values normalized between the target_min and target_max.

  Example input: 
    d = {'a':1.2,'b':3.4,'c':5.6,'d':7.8}
    target_min = -5
    target_max = 5
  """
  min_val = min(val for val in d.values())
  max_val = max(val for val in d.values())
  range_val = max_val - min_val

  if range_val == 0: 
    for key, val in d.items(): 
      d[key] = (target_max - target_min)/2
  else: 
    for key, val in d.items():
      d[key] = ((val - min_val) * (target_max - target_min) 
                / range_val + target_min)
  return d


def top_highest_x_values(d, x):
  """
  This function takes a dictionary 'd' and an integer 'x' as input, and 
  returns a new dictionary containing the top 'x' key-value pairs from the 
  input dictionary 'd' with the highest values.

  INPUT: 
    d: Dictionary. The input dictionary from which the top 'x' key-value pairs 
       with the highest values are to be extracted.
    x: Integer. The number of top key-value pairs with the highest values to
       be extracted from the input dictionary.
  OUTPUT: 
    A new dictionary containing the top 'x' key-value pairs from the input 
    dictionary 'd' with the highest values.
  
  Example input: 
    d = {'a':1.2,'b':3.4,'c':5.6,'d':7.8}
    x = 3
  """
  top_v = dict(sorted(d.items(), 
                      key=lambda item: item[1], 
                      reverse=True)[:x])
  return top_v


def extract_recency(persona, nodes):
  """
  获取当前 Persona 对象和按时间顺序排列的节点列表，并输出包含计算出的
  时近性分数的字典。

  输入: 
    persona: 我们正在检索其记忆的当前智能体。
    nodes: 按时间顺序排列的节点对象列表。
  输出: 
    recency_out: 字典，其键为 node.node_id，值为表示时近性分数的浮点数。
  """
  recency_vals = [persona.scratch.recency_decay ** i 
                  for i in range(1, len(nodes) + 1)]
  
  recency_out = dict()
  for count, node in enumerate(nodes): 
    recency_out[node.node_id] = recency_vals[count]

  return recency_out


def extract_importance(persona, nodes):
  """
  Gets the current Persona object and a list of nodes that are in a 
  chronological order, and outputs a dictionary that has the importance score
  calculated.

  INPUT: 
    persona: Current persona whose memory we are retrieving. 
    nodes: A list of Node object in a chronological order. 
  OUTPUT: 
    importance_out: A dictionary whose keys are the node.node_id and whose 
                    values are the float that represents the importance score.
  """
  importance_out = dict()
  for count, node in enumerate(nodes): 
    importance_out[node.node_id] = node.poignancy

  return importance_out


def extract_relevance(persona, nodes, focal_pt): 
  """
  Gets the current Persona object, a list of nodes that are in a 
  chronological order, and the focal_pt string and outputs a dictionary 
  that has the relevance score calculated.

  INPUT: 
    persona: Current persona whose memory we are retrieving. 
    nodes: A list of Node object in a chronological order. 
    focal_pt: A string describing the current thought of revent of focus.  
  OUTPUT: 
    relevance_out: A dictionary whose keys are the node.node_id and whose values
                 are the float that represents the relevance score. 
  """
  focal_embedding = get_embedding(focal_pt)

  relevance_out = dict()
  for count, node in enumerate(nodes): 
    node_embedding = persona.a_mem.embeddings[node.embedding_key]
    relevance_out[node.node_id] = cos_sim(node_embedding, focal_embedding)

  return relevance_out


def new_retrieve(persona, focal_points, n_count=30): 
  """
  给定当前智能体和焦点（焦点是我们要检索的事件或思考），我们为每个焦点检索
  一组节点并返回一个字典。

  输入: 
    persona: 我们正在检索其记忆的当前智能体对象。
    focal_points: 焦点列表（作为当前检索焦点的事件或思考的字符串描述）。
  输出: 
    retrieved: 字典，其键为字符串焦点，值为智能体联想记忆中的节点对象列表。

  输入示例:
    persona = <persona> 对象 
    focal_points = ["How are you?", "Jane is swimming in the pond"]
  """
  # <retrieved> 是我们返回的主要字典
  retrieved = dict() 
  for focal_pt in focal_points: 
    # 从智能体的记忆中获取所有节点（思考和事件），并按创建的日期时间排序。
    # 你也可以想象获取原始对话，但目前先这样。
    nodes = [[i.last_accessed, i]
              for i in persona.a_mem.seq_event + persona.a_mem.seq_thought
              if "idle" not in i.embedding_key]
    nodes = sorted(nodes, key=lambda x: x[0])
    nodes = [i for created, i in nodes]

    # 计算组件字典并对其进行归一化。
    recency_out = extract_recency(persona, nodes)
    recency_out = normalize_dict_floats(recency_out, 0, 1)
    importance_out = extract_importance(persona, nodes)
    importance_out = normalize_dict_floats(importance_out, 0, 1)  
    relevance_out = extract_relevance(persona, nodes, focal_pt)
    relevance_out = normalize_dict_floats(relevance_out, 0, 1)

    # 计算结合组件值的最终分数。
    # 自我提醒：测试不同的权重。[1, 1, 1] 通常工作得相当好，
    # 但在未来，这些权重可能应该通过类似 RL 的过程来学习。
    # gw = [1, 1, 1]
    # gw = [1, 2, 1]
    gw = [0.5, 3, 2]
    master_out = dict()
    for key in recency_out.keys(): 
      master_out[key] = (persona.scratch.recency_w*recency_out[key]*gw[0] 
                     + persona.scratch.relevance_w*relevance_out[key]*gw[1] 
                     + persona.scratch.importance_w*importance_out[key]*gw[2])

    master_out = top_highest_x_values(master_out, len(master_out.keys()))
    for key, val in master_out.items(): 
      print (persona.a_mem.id_to_node[key].embedding_key, val)
      print (persona.scratch.recency_w*recency_out[key]*1, 
             persona.scratch.relevance_w*relevance_out[key]*1, 
             persona.scratch.importance_w*importance_out[key]*1)

    # 提取最高的 x 个值。
    # <master_out> 具有 node.id 的键和浮点数的值。一旦我们得到最高的 x 个值，
    # 我们希望将 node.id 转换为节点并返回节点列表。
    master_out = top_highest_x_values(master_out, n_count)
    master_nodes = [persona.a_mem.id_to_node[key] 
                    for key in list(master_out.keys())]

    for n in master_nodes: 
      n.last_accessed = persona.scratch.curr_time
      
    retrieved[focal_pt] = master_nodes

  return retrieved













