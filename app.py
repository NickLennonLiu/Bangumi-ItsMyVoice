"""
Gradio Interface for AniVoice
"""

import gradio as gr
import toml
import subprocess
import os
from utils import path_util
from episode import get_demo_episode
from subtitle import extract_mkv_subtitle_info, extract_subtitles, load_subtitle, split_mkv_audio_by_subevent

# 全局变量
config = toml.load("config.toml")

global_vars = dict(
    track_id=0,
    anime_name=config["anime"]["anime_name"],
    anime_folder=config["anime"]["anime_folder"],
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


def step1():
    """
    第一步：获取番剧的字幕轨道信息
    """
    step1_block = gr.Blocks()
    with step1_block:
        gr.Markdown("# Step 1: Get Subtitle Track Info")
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
        gr.Markdown("# Step 2: Extract Subtitles")
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
        gr.Markdown("# Step 2.5: Process ASS Subtitle")
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
                    # lns_dict[key] = [value[0], value[-1]]
            
                return "\n".join(output_texts)
            
            get_layers_btn.click(fn=get_ass_info, 
                                 inputs=demo_sub_textbox,
                                 outputs=[lns_info])
    
    return step2_5_ass_block        
    
def start_uvr5_webui():
    # 获得当前python位置
    import sys
    python_exec = sys.executable
    print(python_exec)
    cmd = f"\"{python_exec}\" Tools\\uvr5\\webui.py \"cpu\" False 23333 False"
    print(cmd)
    subprocess.Popen(args=['chdir'], shell=True)
    subprocess.Popen(args=[cmd], shell=True)

def extract_wav():
    pass

def step3():
    """
    第三步: 对番剧的音频进行UVR5
    """
    step3_block = gr.Blocks()
    with step3_block:
        with gr.Column():
            extract_audio_btn = gr.Button("Extract Audio")
            extract_audio_btn.click(fn=extract_wav)
            gr.Text("未实现，请自行处理，导出到audio文件夹",
                    label="UVR5")
            
def split_audio(audio_folder, subtitle_folder, sub_type):
    for audio_file, sub_file in zip(os.listdir(audio_folder), os.listdir(subtitle_folder)):
        audio_path = os.path.join(audio_folder, audio_file)
        sub_path = os.path.join(subtitle_folder, sub_file)
        print(audio_path, sub_path)
        events = load_subtitle(sub_path, sub_type)
        split_mkv_audio_by_subevent(global_vars["anime_name"], audio_path, events)
        break
    
def step4():
    """
    根据字幕文件对文件进行切分
    """
    step4_block = gr.Blocks()
    with step4_block:
        audio_folder = gr.Textbox(label="Audio Folder")
        subtitle_folder = gr.Textbox(label="Subtitle Folder")
        sub_type = gr.Radio(label="Subtitle Type", choices=['srt', 'ass'])
        split_btn = gr.Button("Split Audio")
        result_box = gr.Textbox(label="Split Result", value="Click 'Split Audio' to split audio")
        split_btn.click(fn=split_audio, 
                        inputs=[audio_folder, subtitle_folder, sub_type], 
                        outputs=result_box)

def main_interface():
    """Merge all steps into columns"""
    main_block = gr.Blocks()
    with main_block:
        step1_block = step1()
        step2_block = step2()
        step2_5_ass_block = step2_5_ass()
        step3_block = step3()
        step4_block = step4()

    return main_block


demo = main_interface()

demo.launch()
