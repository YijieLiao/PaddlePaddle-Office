# coding=utf-8

from openai import OpenAI
import erniebot
from socketplus import *
import re
import ast

erniebot.api_type = 'aistudio'
erniebot.access_token = '51cdf5cac497428374ff7204e9e25ba85452dc12'

client = OpenAI(
    api_key="51cdf5cac497428374ff7204e9e25ba85452dc12",
    # 含有 AI Studio 访问令牌的环境变量，https://aistudio.baidu.com/account/accessToken,
    base_url="https://aistudio.baidu.com/llm/lmapi/v3",  # aistudio 大模型 api 服务域名
)

systems = """作为公司CEO，你需根据任务需求为固定员工分配角色和任务。以下是严格规则：

# 员工名单
刘一、陈二、张三、李四、王五、赵六、孙七、周八、吴九、郑十

# 强制规则
1. 角色命名：身份+姓名（如「设计师张三」），职务需符合任务需求
2. 任务分配：
   - 必须覆盖全部10名员工
   - 任务描述需包含跨角色协作（如"与李四确认设计方案"）
   - 每日进度递增：50%/100%
3. 空间限制：
   电脑室、会议室、电话室、财务室、档案室、会客厅、茶水间、面试间（只能选择这其中的）
4. 表情符号：
   - 每个任务严格使用2个emoji
   - 禁止文字符号（如📋应改用📄）
   - 示例：😊💻表示愉快+电脑工作
5. 注意要按照2天的形式分配，第一次是输出第一天的，当我说“继续”的时候，才输出下一天的，不允许两天一起输出
6. 每一天人物都要换一个位置，这个位置必须是空间限制内的位置，而不是呆在原地不动
7. 特别注意只允许按照这样的样例，就算是第二天，也不允许出现其他东西，不允许备注，注意等等内容出现
# 输出格式（严格JSON）
'''json
{
  "task": "任务名称",
  "process": "当前百分比进度",
  "time": "第n天",
  "tasks": [
    {
      "name": "员工姓名",
      "position": "角色职位",
      "to": "指定房间",
      "do_": "详细任务描述（包含协作对象）",
      "emoji": "两个表情"
    },
    // 必须包含10个对象
  ]
}
'''

# 优质示例
{
  "task": "新产品发布会",
  "process": "50%",
  "time": "1",
  "tasks": [
    {
      "name": "张三",
      "position": "视觉设计师",
      "to": "电脑室",
      "do_": "设计主视觉方案，需与李四（文案策划）确认标语内容",
      "emoji": "🎨💻"
    },
    {
      "name": "李四",
      "position": "文案策划",
      "to": "会议室",
      "do_": "撰写发布会演讲稿，需收集王五（市场分析）提供的用户数据",
      "emoji": "📝👥"
    }
    // 其他8个任务...
  ]
}

请特别注意：
1. 键名使用双引号
2. 房间名称严格匹配，严格遵循空间限制
3. 表情符号间用空格分隔
4. process 字段必须以字符串形式返回，如 "50%"，否则将无法解析！
"""

messages = [
    {
        "role": "user",
        "content": systems
    },
    {
        "role": "assistant",
        "content": "请输入你的具体任务"
    }
]

json_block_regex = re.compile(r"```(.*?)```", re.DOTALL)


def extract_json(content):
    json_blocks = json_block_regex.findall(content)
    if json_blocks:
        full_json = "\n".join(json_blocks)
        if full_json.startswith("json"):
            full_json = full_json[5:]
        return full_json
    else:
        return None


def string_to_dict(dict_string):
    try:
        dictionary = ast.literal_eval(dict_string)
        return dictionary
    except (SyntaxError, ValueError) as e:
        print(f"转换字符串为字典时出错: {e}")
        return None


def replace_key(dictionary, old_key, new_key):
    if old_key in dictionary:
        dictionary[new_key] = dictionary[old_key]
        del dictionary[old_key]
    else:
        print(f"Key '{old_key}' not found in the dictionary.")


def percentage_to_number(s):
    no_percent = s.replace('%', '')
    return int(no_percent)


def to_number(s):
    return int(s)


def cheak(response):
    if response["process"] == 100:
        return True
    else:
        return False


def chat(message):
    if isinstance(message, str):
        message = {"role": "user", "content": message}
    messages.append(message)

    response = erniebot.ChatCompletion.create(
        model='ernie-3.5',
        messages=messages,
        top_p=0
    )
    result = response.get_result()

    messages.append(
        {
            "role": "assistant",
            "content": result,
        }
    )
    return result


def extract_info(json_str):
    try:
        if json_str["type"] == "question":
            return True, json_str["question"]
        if json_str["type"] == "response":
            return False, json_str["response"]
    except json.JSONDecodeError as e:
        return f"Error  JSON: {e}"


def remove_text_spaces_keep_emojis_v2(task_data):
    for task in task_data['tasks']:
        # Remove all alphabetic characters and spaces from the 'emoji' field
        task['emoji'] = ''.join(char for char in task['emoji'] if not char.isalpha() and not char.isspace())

    return task_data


def trim_emoji(tasks):
    for task in tasks:
        if len(task['emoji']) > 5:
            task['emoji'] = task['emoji'][:5]  # Keep only the first 5 characters
    return tasks


socketserver = socketclient('127.0.0.1', 12339)


def main():
    while True:
        try:
            recv_data = socketserver.recv()
            print(recv_data)
            if recv_data != False:
                break
        except Exception as e:
            return f"Error  JSON: {e}"

    type, question = extract_info(recv_data)
    for index in range(50):
        if index == 0:
            if type == True:
                response = chat(question)
        else:
            response = chat("继续")

        print(response)
        json = extract_json(response)
        json = string_to_dict(json)
        json["time"] = to_number(json["time"])
        json["process"] = percentage_to_number(json["process"])
        json = remove_text_spaces_keep_emojis_v2(json)
        # json = trim_emoji(json['tasks'])
        new = {'resultType': 'task', 'closingReport': ''}
        json = {**new, **json}
        # print(json)
        socketserver.send(json)

        stop = cheak(json)
        if stop == True:
            response = chat("请基于本任务在完成过程中全部员工的工作内容，做一个结项报告书。要求语言简短，不需要生成句号，记得及时换行。\
                            格式如下：\
                            任务名称：\
                            所有参与员工及在这个任务中所做事宜与对这个员工的评价(不超过一行)：\
                            整体工作内容概况：")
            new = {'resultType': 'closingReport', 'closingReport': response}
            socketserver.send(new)
            print(response)
            break

        # 每天日报发送完后，服务端阻塞等待 Unity 用户点击“继续”
        while True:
            recv_data = socketserver.recv()
            type, res = extract_info(recv_data)
            if type == False:
                if res == True:
                    break


if __name__ == "__main__":
    main()