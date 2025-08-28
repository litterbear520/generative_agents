"""
作者: Joon Sung Park (joonspk@stanford.edu)

文件: perceive.py
描述: 定义生成式智能体的"感知"模块。
"""
import sys
sys.path.append('../../')

from operator import itemgetter
from global_methods import *
from persona.prompt_template.gpt_structure import *
from persona.prompt_template.run_gpt_prompt import *

def generate_poig_score(persona, event_type, description): 
  if "is idle" in description: 
    return 1

  if event_type == "event": 
    return run_gpt_prompt_event_poignancy(persona, description)[0]
  elif event_type == "chat": 
    return run_gpt_prompt_chat_poignancy(persona, 
                           persona.scratch.act_description)[0]

def perceive(persona, maze): 
  """
  感知智能体周围的事件并将其保存到记忆中，包括事件和空间信息。

  我们首先感知智能体附近的事件，由其 <vision_r> 视野半径决定。如果该半径内
  发生了很多事件，我们会取 <att_bandwidth> 个最近的事件。最后，我们检查
  其中是否有新事件，由 <retention> 保留期决定。如果它们是新的，那么我们
  保存这些事件并返回这些事件的 <ConceptNode> 实例。

  输入: 
    persona: 表示当前智能体的 <Persona> 实例。
    maze: 表示智能体正在其中行动的当前迷宫的 <Maze> 实例。
  输出: 
    ret_events: 被感知到的新 <ConceptNode> 列表。
  """
  # 感知空间
  # 根据我们当前的瓦片位置和智能体的视野半径，获取附近的瓦片。
  nearby_tiles = maze.get_nearby_tiles(persona.scratch.curr_tile, 
                                       persona.scratch.vision_r)

  # 然后我们存储感知到的空间。注意智能体的 s_mem 是使用字典构建的树形结构。 
  for i in nearby_tiles: 
    i = maze.access_tile(i)
    if i["world"]: 
      if (i["world"] not in persona.s_mem.tree): 
        persona.s_mem.tree[i["world"]] = {}
    if i["sector"]: 
      if (i["sector"] not in persona.s_mem.tree[i["world"]]): 
        persona.s_mem.tree[i["world"]][i["sector"]] = {}
    if i["arena"]: 
      if (i["arena"] not in persona.s_mem.tree[i["world"]]
                                              [i["sector"]]): 
        persona.s_mem.tree[i["world"]][i["sector"]][i["arena"]] = []
    if i["game_object"]: 
      if (i["game_object"] not in persona.s_mem.tree[i["world"]]
                                                    [i["sector"]]
                                                    [i["arena"]]): 
        persona.s_mem.tree[i["world"]][i["sector"]][i["arena"]] += [
                                                             i["game_object"]]

  # 感知事件
  # 我们将感知发生在智能体当前竞技场相同竞技场中的事件。
  curr_arena_path = maze.get_tile_path(persona.scratch.curr_tile, "arena")
  # 我们不会感知同一个事件两次（如果一个物体跨越多个瓦片，可能会发生这种情况）。
  percept_events_set = set()
  # 我们将根据距离对感知进行排序，最近的事件获得优先级。
  percept_events_list = []
  # 首先，我们将附近瓦片中发生的所有事件放入 percept_events_list
  for tile in nearby_tiles: 
    tile_details = maze.access_tile(tile)
    if tile_details["events"]: 
      if maze.get_tile_path(tile, "arena") == curr_arena_path:  
        # 计算智能体当前瓦片与目标瓦片之间的距离。
        dist = math.dist([tile[0], tile[1]], 
                         [persona.scratch.curr_tile[0], 
                          persona.scratch.curr_tile[1]])
        # 将任何相关事件及其距离信息添加到我们的临时集合/列表中。 
        for event in tile_details["events"]: 
          if event not in percept_events_set: 
            percept_events_list += [[dist, event]]
            percept_events_set.add(event)

  # 我们排序并只感知最近的 persona.scratch.att_bandwidth 个事件。
  # 如果带宽更大，则意味着智能体可以在小范围内感知更多元素。
  percept_events_list = sorted(percept_events_list, key=itemgetter(0))
  perceived_events = []
  for dist, event in percept_events_list[:persona.scratch.att_bandwidth]: 
    perceived_events += [event]

  # 存储事件
  # <ret_events> 是来自智能体联想记忆的 <ConceptNode> 实例列表。 
  ret_events = []
  for p_event in perceived_events: 
    s, p, o, desc = p_event
    if not p: 
      # 如果物体不存在，那么我们将事件默认为"idle"。
      p = "is"
      o = "idle"
      desc = "idle"
    desc = f"{s.split(':')[-1]} is {desc}"
    p_event = (s, p, o)

    # 我们检索最新的 persona.scratch.retention 个事件。如果发生了新事情
    # （即 p_event 不在 latest_events 中），那么我们将该事件添加到 a_mem 并返回它。 
    latest_events = persona.a_mem.get_summarized_latest_events(
                                    persona.scratch.retention)
    if p_event not in latest_events:
      # 我们首先管理关键词。
      keywords = set()
      sub = p_event[0]
      obj = p_event[2]
      if ":" in p_event[0]: 
        sub = p_event[0].split(":")[-1]
      if ":" in p_event[2]: 
        obj = p_event[2].split(":")[-1]
      keywords.update([sub, obj])

      # 获取事件嵌入
      desc_embedding_in = desc
      if "(" in desc: 
        desc_embedding_in = (desc_embedding_in.split("(")[1]
                                              .split(")")[0]
                                              .strip())
      if desc_embedding_in in persona.a_mem.embeddings: 
        event_embedding = persona.a_mem.embeddings[desc_embedding_in]
      else: 
        event_embedding = get_embedding(desc_embedding_in)
      event_embedding_pair = (desc_embedding_in, event_embedding)
      
      # 获取事件重要性。
      event_poignancy = generate_poig_score(persona, 
                                            "event", 
                                            desc_embedding_in)

      # 如果我们观察到智能体的自我对话，我们在这里将其包含在智能体的记忆中。 
      chat_node_ids = []
      if p_event[0] == f"{persona.name}" and p_event[1] == "chat with": 
        curr_event = persona.scratch.act_event
        if persona.scratch.act_description in persona.a_mem.embeddings: 
          chat_embedding = persona.a_mem.embeddings[
                             persona.scratch.act_description]
        else: 
          chat_embedding = get_embedding(persona.scratch
                                                .act_description)
        chat_embedding_pair = (persona.scratch.act_description, 
                               chat_embedding)
        chat_poignancy = generate_poig_score(persona, "chat", 
                                             persona.scratch.act_description)
        chat_node = persona.a_mem.add_chat(persona.scratch.curr_time, None,
                      curr_event[0], curr_event[1], curr_event[2], 
                      persona.scratch.act_description, keywords, 
                      chat_poignancy, chat_embedding_pair, 
                      persona.scratch.chat)
        chat_node_ids = [chat_node.node_id]

      # 最后，我们将当前事件添加到智能体的记忆中。 
      ret_events += [persona.a_mem.add_event(persona.scratch.curr_time, None,
                           s, p, o, desc, keywords, event_poignancy, 
                           event_embedding_pair, chat_node_ids)]
      persona.scratch.importance_trigger_curr -= event_poignancy
      persona.scratch.importance_ele_n += 1

  return ret_events




  











