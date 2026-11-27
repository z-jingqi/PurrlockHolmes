# 福尔猫斯 · Purrlock Holmes

**午后客厅。** [在网页试玩](https://purrlock-holmes.pineappleq16.workers.dev/)。拖动查看房间，点桌子、椅子和柜子收起家具。物品沿弧线飞入猫爪收纳匣，入匣后计数。失去支撑的小物件受重力和碰撞影响，桌沿毛巾也会落下。点击提示后，目标周围的光线顺时针旋转，目标轻轻呼吸。没有镜头旋转、视差或倒计时。

## 场景和素材

Godot 4.7.2 导入项目后按 F5。原房间固定背景从 Blender 烘焙，保留柔和的灯光；家具静止和收纳时共用同一张 Blender 图，碰撞仍由独立的 3D 支撑体计算。小物件采用各自的质量、受风面积、摩擦和回弹，使用同一世界重力。毛巾是可变形网格，与桌沿、桌面、地面接触；不与全部小道具做双向碰撞。剩余目标在掉落后检查可点击范围，目标是至少保留 25% 的投影点击轮廓。网页与桌面共用同一个关卡。

修改 `art/room.blend` 后重出素材：

```sh
blender -b art/room.blend --python art/export_room.py
```

`art/build_room.py` 可从零重建房间。字体授权见 `game/NotoSansCJK-OFL.txt`。iOS 真机尚未验证。

## 构建和部署

```sh
godot --headless --path . --import
godot --headless --path . -- --test-furniture
python3 tools/fetch-godot-web-template.py 4.7.2 /tmp/purrlock-web.zip
GODOT_WEB_TEMPLATE=/tmp/purrlock-web.zip sh tools/build-web.sh
node tools/test-worker.mjs
npx wrangler dev
```

网页版需要 WebGL 2。GitHub Actions 检查六种家具收纳顺序并构建同一关卡；Cloudflare 自动发布需要仓库 Actions Secret `CLOUDFLARE_API_TOKEN` 和 Variable `CLOUDFLARE_ACCOUNT_ID`。
