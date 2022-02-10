# 开发环境

### 安装 MongoDB
  - brew 安装比较慢，可以去官网下载安装包安装
  - 使用默认配置，不设密码
  - 创建本地数据库 hyle

### 安装 Python3
  ```bash
  brew install python3
  ```

### 安装 pip3
  方法见 https://pip.pypa.io/en/stable/installing

### 设置 pip 国内镜像
  - 找到配置文件, 一般在 `~/.config/pip/pip.conf`
  - 加上下面的配置
    ```
    [global]
    index-url=https://pypi.tuna.tsinghua.edu.cn/simple

    [install]
    trusted-host=pypi.tuna.tsinghua.edu.cn
    ```

### 安装 virtualenv
  ```bash
  pip3 install virtualenv
  ```

### 创建虚拟环境
  ```bash
  cd 到项目目录
  virtualenv --python=python3 ./venv
  ```

### 安装 Python Package
  ```bash
  . ./venv/bin/activate
  pip3 install -r requirement.txt
  ```

### 下载数据
运行脚本 devops/init.sh
```bash
sh devops/download.sh
```

### 整合数据
运行脚本 devops/integrate.sh
```bash
sh devops/integrate.sh
```

### 启动前端服务
```bash
sh devops/run.sh
```

### 访问前端地址
- 基金持仓    http://localhost:5000/fund-house/position
- 个股基金仓位 http://localhost:5000/stock/fundpos/{stock_code}
