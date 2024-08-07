import os, subprocess, chardet, toml

config = toml.load('config.toml')

def path_util(filename, abbrs, ext=None):
    """
    给定某个文件的文件名（不包含其目录），生成一个对应的新的文件路径。
    """
    if isinstance(abbrs, str):
        abbrs = [abbrs]
        
    filename = os.path.basename(filename)
    
    output_path = config['path']['output_folder']
    path = os.path.join(output_path, *abbrs, filename)
    folder = os.path.dirname(path)
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    if ext:
        path = os.path.splitext(path)[0] + ext
    
    return path

def folder_util(abbrs):
    """
    根据abbrs生成一个文件夹路径
    """
    if isinstance(abbrs, str):
        abbrs = [abbrs]
    
    output_path = config['path']['output_folder']
    path = os.path.join(output_path, *abbrs)
    if not os.path.exists(path):
        os.makedirs(path)
    
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
    if err:
        encoding = chardet.detect(err)
        if encoding['encoding'] is None:
            encoding['encoding'] = 'utf-8'
        try:
            print(err.decode(encoding['encoding'], errors='ignore'))
        except:
            print(err.decode('utf-8', errors='ignore'))
    return result


# 写一个装饰器函数，对于给定一个函数，如果发生了报错，返回报错内容，否则返回函数的返回值
def catch_error(fn):
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            # raise e
            return str(e)
    return wrapper