import os

def get_demo_episode(anime_folder):
    # list all mkv files and sort
    episodes = sorted([f for f in os.listdir(anime_folder) if f.endswith('.mkv')])
    # show mkv subtitles infos
    demo_episode = episodes[0]
    return os.path.join(anime_folder, demo_episode)

def get_episodes(anime_folder):
    episodes = sorted([os.path.join(anime_folder, f) for f in os.listdir(anime_folder) if f.endswith('.mkv')])
    return episodes