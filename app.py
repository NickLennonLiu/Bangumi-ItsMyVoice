"""
Gradio Interface for AniVoice
"""

import gradio as gr
import toml
import subprocess
import os
from utils import path_util, folder_util, exec_cmd
from episode import get_demo_episode
from subtitle import extract_mkv_subtitle_info, extract_subtitles, \
                        load_subtitle, select_subtitles_by_lns, split_mkv_audio_by_subevent, \
                        get_ass_info

# 全局变量
config = toml.load("config.toml")

global_vars = dict(
    track_id=0,
    anime_name=config["anime"]["anime_name"],
    anime_folder=config["anime"]["anime_folder"]
)


def update_global_vars(key):
    def update_function(value):
        global global_vars
        global_vars[key] = value
    return update_function


def get_subtitle_track_info():
    """
    查看番剧的字幕轨道信息
    """
    demo_episode = get_demo_episode(global_vars["anime_folder"])
    result = extract_mkv_subtitle_info(demo_episode)
    return result

def get_default_location_textbox(label, abbrs):
    """
    获得某个项目和某个分类的默认输出目录
    """
    if isinstance(abbrs, str):
        abbrs = [abbrs]
    path = folder_util([global_vars['anime_name']] + abbrs)
    return gr.Textbox(label=label, value=path, interactive=True)

def step1():
    """
    第一步：获取番剧的字幕轨道信息
    """
    step1_block = gr.Blocks()
    with step1_block:
        gr.Markdown("## Step 1: Get Subtitle Track Info")
        with gr.Row():
            anime_name_box = gr.Textbox(
                label="Anime Name", value=global_vars["anime_name"], interactive=True
            )
            anime_folder_box = gr.Textbox(
                label="Anime Folder",
                value=global_vars["anime_folder"],
                interactive=True,
            )
            anime_name_box.change(
                fn=update_global_vars("anime_name"), inputs=anime_name_box, outputs=None
            )
            anime_folder_box.change(
                fn=update_global_vars("anime_folder"),
                inputs=anime_folder_box,
                outputs=None,
            )

        with gr.Row():
            submit_btn = gr.Button(value="Submit")
            result = gr.Textbox(
                label="Subtitle Info",
                value="Click 'Submit' to get subtitle info",
                max_lines=10,
            )
            submit_btn.click(fn=get_subtitle_track_info,
                             inputs=None, outputs=result)


def extract_anime_subtitles(subtitle_type):
    result = extract_subtitles(
        global_vars["anime_folder"], 
        global_vars["anime_name"], 
        global_vars["track_id"],
        subtitle_type
    )
    return result


def step2():
    """
    第二步：提取番剧的字幕文件
    """
    step2_block = gr.Blocks()
    with step2_block:
        gr.Markdown("## Step 2: Extract Subtitles")
        with gr.Row():
            track_id_input = gr.Number(label="Subtitle Track ID", value=0)
            track_id_input.change(
                fn=update_global_vars("track_id"), inputs=track_id_input, outputs=None
            )
            
            subtitle_type = gr.Radio(
                label="Subtitle Type",
                choices=["srt", "ass"],
            )

            extract_btn = gr.Button(value="Extract")
            extract_result = gr.Textbox(
                label="Extract Result",
                value="Click 'Extract' to extract subtitles",
                max_lines=10,
            )
            extract_btn.click(
                fn=extract_anime_subtitles, inputs=[subtitle_type], outputs=extract_result
            )
            
def step2_5_ass():
    """
    第2.5步：对字幕文件进行处理
    """
    step2_5_ass_block = gr.Blocks()
    with step2_5_ass_block:
        gr.Markdown("### Step 2.5: Process ASS Subtitle")
        with gr.Column():
            with gr.Row():
                demo_episode = get_demo_episode(global_vars['anime_folder'])
                demo_episode = os.path.basename(demo_episode)
                demo_sub_file = path_util(demo_episode, 
                                        [global_vars['anime_name'],
                                        'subtitles'],
                                        '.ass'
                                        )
                demo_sub_textbox = gr.Textbox(label='Demo Subtitle',
                                            value=demo_sub_file)
                get_layers_btn = gr.Button()
                lns_info = gr.Textbox(label='Layer/Name/Style Info')
                
                def update_check_group(demo_sub):
                    lns_info, lns_list = get_ass_info(demo_sub)
                    lns_list = [str(item) for item in lns_list]
                    new_chkbox = gr.CheckboxGroup(choices=lns_list, label="Select Options", interactive=True)
                    return lns_info, new_chkbox
                
            with gr.Row():
                # 多选框
                checkbox_group = gr.CheckboxGroup(label="Select (Layer, Name, Style)")
                with gr.Column():
                    sub_before = get_default_location_textbox("Subtitle folder", 'subtitles')
                    sub_after = get_default_location_textbox("Processed Subtitle folder", 'processed_subtitles')
                process_subtitle_btn = gr.Button("Process ASS Subtitles")
                process_result = gr.Textbox(label="Result", value="")
                
                def process_subtitle(before_fold, after_fold, lns_list):
                    lns_list = [eval(option) for option in lns_list]
                    result = select_subtitles_by_lns(before_fold, after_fold, lns_list)
                    return result
                    
            get_layers_btn.click(fn=update_check_group, 
                                    inputs=demo_sub_textbox,
                                    outputs=[lns_info, checkbox_group])
            
            process_subtitle_btn.click(fn=process_subtitle,
                                       inputs=[sub_before, sub_after, checkbox_group],
                                       outputs=process_result)
    
    return step2_5_ass_block        


def step3():
    """
    第三步: 对番剧的音频进行UVR5
    """
    step3_block = gr.Blocks()
    with step3_block:
        gr.Markdown("## Step 3: Extract Vocals")
        gr.Text("未实现，请自行处理，导出到audio文件夹",
                    label="UVR5")
            
def split_audio(audio_folder, subtitle_folder, sub_type):
    for audio_file, sub_file in zip(os.listdir(audio_folder), os.listdir(subtitle_folder)):
        assert os.path.splitext(os.path.basename(sub_file))[0] in os.path.splitext(os.path.basename(audio_file))[0]
        
        audio_path = os.path.join(audio_folder, audio_file)
        sub_path = os.path.join(subtitle_folder, sub_file)
        # print(audio_path, sub_path)
        
        # 从audio_file中获得集数信息，用正则提取\d\d
        import re
        episode_id = str(re.match(r'\d\d', audio_file).group())
        # print(episode_id, audio_file)
        # continue
        
        # continue
        events = load_subtitle(sub_path, sub_type)
        result = split_mkv_audio_by_subevent(global_vars["anime_name"], audio_path, episode_id, events)
    
def step4():
    """
    根据字幕文件对文件进行切分
    """
    step4_block = gr.Blocks()
    with step4_block:
        gr.Markdown("## Step 4: Slice Audio by Subtitle")
        with gr.Row():
            with gr.Column():
                audio_folder = get_default_location_textbox("Audio Folder", "audio")
                subtitle_folder = get_default_location_textbox("Subtitle Folder", "processed_subtitles")
                sub_type = gr.Radio(label="Subtitle Type", choices=['srt', 'ass'], value="ass")
            split_btn = gr.Button("Split Audio")
            result_box = gr.Textbox(label="Split Result", value="Click 'Split Audio' to split audio")
            split_btn.click(fn=split_audio, 
                            inputs=[audio_folder, subtitle_folder, sub_type], 
                            outputs=result_box)

def get_episode_list():
    anime_name = global_vars["anime_name"]
    splits_folder = folder_util([anime_name, "split"])
    # print(splits_folder)
    ep_list = [folder for folder in os.listdir(splits_folder) 
               if os.path.isdir(os.path.join(splits_folder, folder))]
    return ep_list

def main_interface():
    """Merge all steps into columns"""
    main_block = gr.Blocks()
    with main_block:
        with gr.Tabs():
            with gr.Tab(label="Stage 1: Get Splits"):
                step1_block = step1()
                step2_block = step2()
                step2_5_ass_block = step2_5_ass()
                step3_block = step3()
                step4_block = step4()
            with gr.Tab(label="Stage 2: Categorize Splits"):
                
                with gr.Row():
                    def get_label_info():
                        anime_name = global_vars["anime_name"]
                        label_folder = folder_util([anime_name, 'label'])
                        characters = [chara for chara in os.listdir(label_folder)
                                      if os.path.isdir(os.path.join(label_folder, chara))]
                        characters_lens = {
                            chara: len(os.listdir(os.path.join(label_folder, chara)))
                            for chara in characters
                        }
                        return characters_lens, "✅" if len(set(characters_lens.values())) == 1 else "🚫"
                    
                    label_info = gr.Textbox(label="Label Info", value=get_label_info()[0])
                    label_check = gr.Radio(choices=["✅", "🚫"], label="Label Dist Balance?")
                    refresh_label_info = gr.Button(value="Refresh")
                    
                    refresh_label_info.click(fn=get_label_info, inputs=None, outputs=[label_info, label_check])
                    
                
                ep_list = get_episode_list()
                # print(ep_list)
                ep_dropdown = gr.Dropdown(choices=ep_list, label="选择集数")
                
                threshold = gr.Slider(minimum=0, maximum=1, step=0.01, label="Threshold", value=0.6)
                
                cluster_cmd = gr.Textbox(label="First Command to run")
                
                def gen_vpr_command(episode, threshold):
                    if not episode:
                        return ""
                    import sys
                    python_executable = sys.executable
                    anime_name = global_vars["anime_name"]
                    vpr = config['tool']['vpr']
                    vpr_dirname = os.path.dirname(vpr)
                    vpr_basename = os.path.basename(vpr)
                    vpr_model_path = config['tool']['vpr_model_path']
                    input_folder = folder_util([anime_name, 'split', episode])
                    input_folder = os.path.abspath(input_folder)
                    label_folder = folder_util([anime_name, 'label'])
                    label_folder = os.path.abspath(label_folder)
                    output_folder = folder_util([anime_name, 'cluster', episode])
                    output_folder = os.path.abspath(output_folder)   
                    cmd = f"cd \"{vpr_dirname}\" && {python_executable} {vpr_basename} -i \"{input_folder}\" "\
                            f"-o \"{output_folder}\" -l \"{label_folder}\" "\
                            f"-m \"{vpr_model_path}\" -t {threshold}"
                    return cmd
                
                ep_dropdown.change(fn=gen_vpr_command,
                                   inputs=[ep_dropdown, threshold],
                                   outputs=cluster_cmd)
                
                exec_btn = gr.Button("Run Command")
                exec_result = gr.Textbox(label="Execution Result", value="")
                
                def exec_command(cmd):
                    result = exec_cmd(cmd, print_result=True)
                    return result
                    
                exec_btn.click(fn=exec_command,
                               inputs=cluster_cmd,
                              outputs=exec_result)
            
    return main_block


demo = main_interface()

demo.launch()
