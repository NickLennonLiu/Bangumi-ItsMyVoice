import toml
from episode import get_episodes
from utils import *
from tqdm import tqdm
import pyass, pysrt

config = toml.load('config.toml')
mkvinfo = config['tool']['mkvinfo']
ffmpeg = config['tool']['ffmpeg']
mkvextract = config['tool']['mkvextract']

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
    
        
def extract_subtitle(file, anime_name, track_id, subtitle_type):
    filename = os.path.basename(file)
    path = path_util(filename, [anime_name, 'subtitles'], f'.{subtitle_type}')
    if os.path.exists(path):
        return f"{filename} already exists"
    os_cmd = f"{mkvextract} tracks \"{file}\" {track_id}:\"{path}\""
    print(os_cmd)
    result = exec_cmd(os_cmd)
    return result
    
    
def extract_subtitles(anime_folder, anime_name, track_id, subtitle_type):
    episodes = get_episodes(anime_folder)
    results = []
    for file in tqdm(episodes):
        result = extract_subtitle(file, anime_name, track_id, subtitle_type)
        results.append(result)
    return '\n'.join(results)


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
    
def split_mkv_audio_by_subevent(anime_name, audio_file, events):
    slice_list = []
    
    basename = os.path.basename(audio_file)
    ep_name = os.path.splitext(basename)[0]
    
    tot = len(events)
    
    for i, event in tqdm(enumerate(events), total=event):
        # 获取字幕的开始时间和结束时间
        text = event.text
        start_time = event.start
        end_time = event.end
        
        # 转换时间格式为ffmpeg可接受的格式
        start_time_str = str(start_time)
        duration = end_time - start_time
        duration_str = str(duration)
        
        output_file = path_util(f"segment_{i}.wav", [anime_name, 'split', ep_name], '.wav')
        
        os_cmd = f"\"{ffmpeg}\" -i \"{audio_file}\" -ss {start_time_str} -t {duration_str} \"{output_file}\""
        
        exec_cmd(os_cmd, print_result=False)
        
        slice_list.append(f"{output_file}|unknown|{text}")
    
    lst_file = path_util(f"{ep_name}.lst", [anime_name, 'split'], '.lst')
    with open(lst_file, 'w') as f:
        f.write('\n'.join(slice_list))
    
    return slice_list