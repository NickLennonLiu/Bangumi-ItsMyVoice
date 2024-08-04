import os, subprocess, chardet, toml

config = toml.load('config.toml')

def path_util(filename, abbrs, ext=None):
    if isinstance(abbrs, str):
        abbrs = [abbrs]
    
    output_path = config['path']['output_folder']
    path = os.path.join(output_path, *abbrs, filename)
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    if ext:
        path = os.path.splitext(path)[0] + ext
    
    return path

def exec_cmd(cmd, print_result=False):
    p = subprocess.Popen(cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = p.communicate()
    encoding = chardet.detect(out)
    if encoding['encoding'] is None:
        encoding['encoding'] = 'utf-8'
    result = out.decode(encoding['encoding'])
    if print_result:
        print(result)
    return result