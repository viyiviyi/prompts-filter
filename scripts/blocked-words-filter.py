import re
from pathlib import Path
from typing import List

from modules import scripts,shared,script_callbacks
from modules.paths_internal import data_path
DATA_PATH = Path(data_path)

blocked_prompts_txt_file = DATA_PATH.joinpath('blocked_prompts.txt')
blocked_negative_prompts_txt_file = DATA_PATH.joinpath('blocked_negative_prompts.txt')

def setVal():
    global blocked_prompts_txt_file
    global blocked_negative_prompts_txt_file
    blocked_prompts_txt_file = shared.opts.data.get('blocked_prompts_txt_file',blocked_prompts_txt_file)
    blocked_negative_prompts_txt_file = shared.opts.data.get('blocked_negative_prompts_txt_file',blocked_negative_prompts_txt_file)

splitSign = [',','(',')','[',']','{','}',':','>']

def get_prompts_by_file(path:Path):
    if path.exists():
        with path.open('r') as f:
            list = f.readlines()
            return [item.strip().lower() for item in list if item.strip() ]
    else:
        return []


blocked_prompts=get_prompts_by_file(blocked_prompts_txt_file)
blocked_negative_prompts=get_prompts_by_file(blocked_negative_prompts_txt_file)

lora_pattern = r'^<[^<>:]'

# 把字符串处理成tag或符号
def prompts_to_arr(prompts:str):
    ls = []
    is_lora = False
    if prompts:
        word = ''
        for sub in prompts:
            if sub in splitSign:
                if sub == ':' and re.match(lora_pattern, word):
                    is_lora = True
                if not is_lora:
                    ls.append(word)
                    ls.append(sub)
                elif sub == '>':
                    is_lora = False
                    word+=sub
                    ls.append(word)
                else:
                    word+=sub
            else:
                word+=sub
        return []
    return []

def get_prompt(input:str):
    return input

left_symbol = ['[','{','(']
right_symbol = [']','}',')']

# 过滤掉因为删除屏蔽词后留下的空
def join_prompts(prompts:str,next:str):
    item = next
    if re.search(r'^(\s*,\s*)$',item) and re.search(r',\s*$',prompts):
        prompts = re.sub(r',\s*$','',prompts)
        return join_prompts(prompts,next)
    elif re.search(r'^(\s*,\s*)$',item) and prompts[-1] in left_symbol:
        return prompts
    elif not item.strip(' ') and prompts[-1] in left_symbol:
        return prompts
    elif item in right_symbol and prompts[-1] == ',':
        prompts = prompts[:-1]
        return join_prompts(prompts,next)
    elif item in right_symbol and prompts[-1] in left_symbol and right_symbol.index(item) == left_symbol.index(prompts[-1]) :
        prompts = prompts[:-1]
        return prompts
    else:
        prompts += item
    return prompts

def filter_prompts_list(input:List[str],blocked:List[str]):
    out_prompts = [item for item in input if get_prompt(item) not in blocked]
    prompts = ''
    for item in out_prompts:
        prompts = join_prompts(prompts,item)
    return prompts

def filter_prompts(prompts:str,blocked:List[str]):
    if not blocked: return prompts
    return filter_prompts_list(prompts_to_arr(prompts),blocked)

class emptyFilter(scripts.Script):
    def title(self):
        return "过滤屏蔽词"

    def show(self, is_img2img):
        return scripts.AlwaysVisible

    def process(self, p):
        for i in range(len(p.all_prompts)):
            p.all_prompts[i] = filter_prompts(p.all_prompts[i],blocked_prompts)

        for i in range(len(p.all_negative_prompts)):
            p.all_negative_prompts[i] = filter_prompts(p.all_negative_prompts[i],blocked_negative_prompts)

def on_ui_settings():
    section = ("fp", "filter blocked words")
    shared.opts.add_option("blocked_prompts_txt_file", shared.OptionInfo(blocked_prompts_txt_file, "屏蔽词文件路径", section=section))
    shared.opts.add_option("blocked_negative_prompts_txt_file", shared.OptionInfo(blocked_negative_prompts_txt_file, "反向tag的屏蔽词文件路径", section=section))

    shared.opts.onchange('blocked_prompts_txt_file', setVal)
    shared.opts.onchange('blocked_negative_prompts_txt_file', setVal)

script_callbacks.on_ui_settings(on_ui_settings)