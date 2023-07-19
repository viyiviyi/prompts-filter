import re
from pathlib import Path
from typing import List

from modules import script_callbacks, scripts, shared
from modules.paths_internal import data_path

DATA_PATH = Path(data_path)

def get_prompts_by_file(path:Path):
    if path.exists():
        with path.open('r') as f:
            list = f.readlines()
            return [item.strip().lower() for item in list if item.strip() ]
    else:
        return []

blocked_prompts_txt_file = str(DATA_PATH.joinpath('blocked_prompts.txt'))
blocked_negative_prompts_txt_file = str(DATA_PATH.joinpath('blocked_negative_prompts.txt'))

blocked_prompts=get_prompts_by_file(Path(blocked_prompts_txt_file))
blocked_negative_prompts=get_prompts_by_file(Path(blocked_negative_prompts_txt_file))

enable_blocked_prompts = True

def setVal():
    global blocked_prompts_txt_file
    global blocked_negative_prompts_txt_file
    global blocked_prompts
    global blocked_negative_prompts
    global enable_blocked_prompts
    
    blocked_prompts_txt_file = shared.opts.data.get('blocked_prompts_txt_file',blocked_prompts_txt_file)
    blocked_negative_prompts_txt_file = shared.opts.data.get('blocked_negative_prompts_txt_file',blocked_negative_prompts_txt_file)
    blocked_prompts=get_prompts_by_file(Path(blocked_prompts_txt_file))
    blocked_negative_prompts=get_prompts_by_file(Path(blocked_negative_prompts_txt_file))
    
    enable_blocked_prompts = shared.opts.data.get('enable_blocked_prompts',enable_blocked_prompts)


splitSign = [',','(',')','[',']','{','}',':','>','\n']
lora_pattern = r'^[\s]*<[^<>]+'
left_symbol = ['[','{','(']
right_symbol = [']','}',')']

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
                    word = ''
                elif sub == '>':
                    is_lora = False
                    word+=sub
                    ls.append(word)
                    word = ''
                else:
                    word+=sub
            else:
                word+=sub
        return [item.strip(' ') for item in ls if item.strip(' ')]
    return []

def get_prompt(input:str):
    return input.strip().lower()

# 过滤掉因为删除屏蔽词后留下的空
def filter_empty(prompts:List[str],next:str):
    item = get_prompt(next)
    if not prompts: return [next]
    if get_prompt(item) == ',' and get_prompt(prompts[-1]) == ',':
        prompts = prompts[:-1]
        return filter_empty(prompts,next)
    elif get_prompt(item) == ',' and prompts[-1] in left_symbol:
        return prompts
    elif not item.strip(' ') and prompts[-1] in left_symbol:
        return prompts
    elif item in right_symbol and prompts[-1] == ',':
        prompts = prompts[:-1]
        return filter_empty(prompts,next)
    elif item in right_symbol and prompts[-1] in left_symbol and right_symbol.index(item) == left_symbol.index(prompts[-1]) :
        prompts = prompts[:-1]
        return prompts
    else:
        prompts += next
    return prompts

def filter_prompts_list(input:List[str],blocked:List[str]):
    out_prompts = []
    for item in input:
        item = f'{item} ' if item == ',' else f'{item}'
        if enable_blocked_prompts and get_prompt(item) in blocked:
            continue
        if enable_blocked_prompts:
            out_prompts = filter_empty(out_prompts,item)
            continue
        out_prompts.append(item)
    prompts = ''.join(out_prompts)
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
    section = ("prompts-filter", "prompts filter")
    
    shared.opts.add_option("enable_blocked_prompts", shared.OptionInfo(enable_blocked_prompts, "启用屏蔽词过滤", section=section))
    shared.opts.add_option("blocked_prompts_txt_file", shared.OptionInfo(blocked_prompts_txt_file, "屏蔽词文件路径", section=section))
    shared.opts.add_option("blocked_negative_prompts_txt_file", shared.OptionInfo(blocked_negative_prompts_txt_file, "反向tag的屏蔽词文件路径", section=section))
    

    shared.opts.onchange('enable_blocked_prompts', setVal)
    shared.opts.onchange('blocked_prompts_txt_file', setVal)
    shared.opts.onchange('blocked_negative_prompts_txt_file', setVal)

script_callbacks.on_ui_settings(on_ui_settings)