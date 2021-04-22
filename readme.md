# 开发环境

> Python3

> MongoDB

> virtualenv
  ```
  virtualenv --python=python3 ./venv
  ```

> Python Package
  ```
  cd venv
  pip3 install -r requirement.txt
  ```

# 下载数据
运行脚本 devops/init.sh
```
sh devops/init.sh
```

# 启动前端
```
sh devops/run.sh
```

# 访问地址
- 基金持仓 /fundco/position
- 个股基金仓位 /stock/{stock_code}/fundpos
