import toml
from episode import get_episodes
from utils import *
from tqdm import tqdm
import concurrent.futures
import pyass, pysrt
import json

config = toml.load('config.toml')
mkvinfo = config['tool']['mkvinfo']
ffmpeg = config['tool']['ffmpeg']
mkvextract = config['tool']['mkvextract']

@catch_error
def extract_mkv_subtitle_info(file):
    os_cmd = f"{mkvinfo} \"{file}\""
    # os_cmd = f"{mkvextract}"
    # print(os_cmd)
    result = exec_cmd(os_cmd)
    # 找到result中包含'轨道编号'的行
    # print(result)
    
    lines = result.split('\n')
    track_infos = []
    for lid, line in enumerate(lines):
        if '轨道编号' in line and '字幕' in lines[lid+2]:
            print(line)
            print(lines[lid+1])
            print(lines[lid+2])
            print(lines[lid+4])
            print(lines[lid+5])
            print(lines[lid+7])
            print(lines[lid+8])
            print("===============")
            
            track_infos += lines[lid:lid+9]
            track_infos += ['==============']
    return '\n'.join(track_infos)
    
@catch_error        
def extract_subtitle(file, anime_name, track_id, subtitle_type):
    filename = os.path.basename(file)
    path = path_util(filename, [anime_name, 'subtitles'], f'.{subtitle_type}')
    if os.path.exists(path):
        return f"{filename} already exists"
    os_cmd = f"{mkvextract} tracks \"{file}\" {track_id}:\"{path}\""
    print(os_cmd)
    result = exec_cmd(os_cmd)
    return result
    
@catch_error
def extract_subtitles(anime_folder, anime_name, track_id, subtitle_type):
    episodes = get_episodes(anime_folder)
    results = []
    for file in tqdm(episodes):
        result = extract_subtitle(file, anime_name, track_id, subtitle_type)
        results.append(result)
    return '\n'.join(results)

@catch_error
def load_subtitle(subtitle_file, type):
    events = []
    
    if type == 'srt':
        subs = pysrt.open(subtitle_file, encoding='utf-8', error_handling=pysrt.ERROR_LOG)
        return subs
    elif type == 'ass':
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            doc = pyass.load(f)
        return doc.events
    else:
        raise NotImplementedError

@catch_error
def split_mkv_audio_by_subevent(anime_name, audio_file, episode_id, events):
    slice_list = []
    slice_json_list = []
    
    basename = os.path.basename(audio_file)
    ep_name = os.path.splitext(basename)[0]
    
    tot = len(events)
    
    cmd_list = []
    for i, event in tqdm(enumerate(events), total=tot):
        # 获取字幕的开始时间和结束时间
        text = event.text
        start_time = event.start
        end_time = event.end
        
        # 转换时间格式为ffmpeg可接受的格式
        start_time_str = str(start_time)
        duration = end_time - start_time
        duration_str = str(duration)
        
        output_filename = f"{anime_name}_{episode_id}_segment_{i}.wav"
        
        output_file = path_util(output_filename, [anime_name, 'split', ep_name], '.wav')
        slice_list.append(f"{output_file}|unknown|{text}")
        slice_json_list.append({
            "filepath": output_file,
            "filename": output_filename,
            "speaker": "unknown",
            "text": text,
            "duration": duration_str,
        })
        
        if os.path.exists(output_file):
            # print(output_file, "Exists")
            continue
        
        os_cmd = f"\"{ffmpeg}\" -i \"{audio_file}\" -ss {start_time_str} -t {duration_str} \"{output_file}\""
        
        # exec_cmd(os_cmd, print_result=False)
        cmd_list.append(os_cmd)
    
    with concurrent.futures.ThreadPoolExecutor() as executor:
        results = list(executor.map(exec_cmd, cmd_list))
    
    lst_file = path_util(f"{ep_name}.lst", [anime_name, 'split'], '.lst')
    json_file = path_util(f"{ep_name}.json", [anime_name, 'split'], '.json')
    with open(lst_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(slice_list))
    
    with open(json_file, 'w', encoding='utf-8') as f:
        json.dump(slice_json_list, f, ensure_ascii=False, indent=4)
    
    return slice_list
    # return '\n'.join(results)

@catch_error
def get_ass_info(sub_file):
    import pyass
    with open(sub_file, 'r', encoding='utf-8') as f:
        sub_data = pyass.load(f)
    layer_name_style = set([(event.layer, event.name, event.style) for event in sub_data.events])
    lns_dict = {
        (l,n,s): [event.text for event in sub_data.events if event.layer == l and event.name == n and event.style == s] for (l, n, s) in layer_name_style
    }
    
    output_texts = []
    for key, value in lns_dict.items():
        output_texts.append(str(key))
        output_texts.append(f"First Sub:\t{value[0]}")
        output_texts.append(f"Last Sub:\t{value[-1]}")

    return "\n".join(output_texts), list(layer_name_style)

@catch_error
def select_subtitles_by_lns(before_fold, after_fold, lns_list):
    for sub_file in os.listdir(before_fold):
        sub_filename = os.path.join(before_fold, sub_file)
        
        with open(sub_filename, 'r', encoding='utf-8') as f:
            sub_data = pyass.load(f)
        
        event_list = [
            event for event in sub_data.events 
            if (event.layer, event.name, event.style) in lns_list
        ]
        
        sub_data.events = event_list
        
        with open(os.path.join(after_fold, sub_file), 'w', encoding='utf-8') as f:
            f.write(sub_data.dumps())
    
    return "Success!"
    