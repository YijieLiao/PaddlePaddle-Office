# test_erniebot_simple.py
import erniebot

erniebot.api_type = 'aistudio'
erniebot.access_token = '51cdf5cac497428374ff7204e9e25ba85452dc12'

response_stream = erniebot.ChatCompletion.create(
    model="ernie-speed",
    messages=[
        {"role": "user", "content": "假如我使用erniebotsdk，我的systems内容很大，会导致超时吗？"}],
    stream=True
)
for response in response_stream:
    print(response.get_result(), end='', flush=True)
print("")
