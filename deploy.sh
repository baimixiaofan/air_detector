#!/bin/bash
# 一键部署脚本 — 本地构建前端 + 上传后端/前端 + 重启服务
# 用法：在项目根目录执行 bash deploy.sh

set -e

SERVER="root@47.109.191.13"
REMOTE_FLASK="/home/flask_app"
REMOTE_DIST="/home/flask_app/web-admin/dist"

echo "============================"
echo "1. 本地构建前端"
echo "============================"
cd web-admin
npm run build
cd ..
echo "✅ 前端构建完成"

echo "============================"
echo "2. 上传前端文件"
echo "============================"
ssh $SERVER "cd $REMOTE_DIST && rm -f index.html favicon.svg icons.svg && rm -rf assets"
scp -r web-admin/dist/* $SERVER:$REMOTE_DIST/
echo "✅ 前端上传完成"

echo "============================"
echo "3. 上传后端文件"
echo "============================"
scp server/admin_api.py         $SERVER:$REMOTE_FLASK/
scp server/flask_api_server.py  $SERVER:$REMOTE_FLASK/
scp server/miniprogram_api.py   $SERVER:$REMOTE_FLASK/
scp server/consumer.py          $SERVER:$REMOTE_FLASK/
scp server/config.py            $SERVER:$REMOTE_FLASK/
scp server/daily_stats_job.py   $SERVER:$REMOTE_FLASK/
scp server/db_migrate.py        $SERVER:$REMOTE_FLASK/
scp server/alert_checker.py     $SERVER:$REMOTE_FLASK/
echo "✅ 后端上传完成"

echo "============================"
echo "4. 执行数据库迁移"
echo "============================"
# db_migrate.py 需要上传后执行，找 Python 环境
PYTHON_CMD=""
for try_path in \
    "/var/lib/jenkins/workspace/test/venv/bin/python" \
    "/home/flask_app/venv/bin/python" \
    "$(ssh $SERVER 'which python3 2>/dev/null')"; do
    if [ -n "$try_path" ] && ssh $SERVER "test -x $try_path" 2>/dev/null; then
        PYTHON_CMD="$try_path"
        break
    fi
done
if [ -n "$PYTHON_CMD" ]; then
    ssh $SERVER "cd $REMOTE_FLASK && $PYTHON_CMD db_migrate.py"
    echo "✅ 数据库迁移完成"
else
    echo "⚠️ 未找到 Python 环境，尝试默认 python3"
    ssh $SERVER "cd $REMOTE_FLASK && python3 db_migrate.py" 2>/dev/null \
      && echo "✅ 数据库迁移完成" \
      || echo "⚠️ 迁移跳过（手动：ssh $SERVER cd $REMOTE_FLASK && python3 db_migrate.py）"
fi

echo "============================"
echo "5. 重启 Flask 服务"
echo "============================"
ssh $SERVER "systemctl restart flask_api"
sleep 2
if ssh $SERVER "systemctl is-active --quiet flask_api"; then
    echo "✅ Flask API 启动成功"
else
    echo "❌ Flask API 启动失败，请检查日志："
    echo "   ssh $SERVER 'journalctl -u flask_api -n 20'"
    exit 1
fi

echo ""
echo "============================"
echo "✅ 部署完成！"
echo "============================"
echo "管理后台: https://baimeixiaofan.xyz/admin/"
echo "监控面板: https://baimeixiaofan.xyz/monitor"
