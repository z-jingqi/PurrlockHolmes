# 福尔猫斯 · Purrlock Holmes

**案卷 01：茶点过后。** [在网页试玩](https://purrlock-holmes.pineappleq16.workers.dev/)。
拖动查看午后的客厅，点按收起六件餐具。每一关的目标分类从开场固定到通关；本关始终是「餐具」，不需要搬走家具。点中的道具先浮起，再沿弧线飞入猫爪收纳匣，入匣才计数。提示会照亮未收集物品；可交互的干扰道具只短暂晃动。

## 运行与验证

用 Godot 4.7.2 导入项目后按 F5。网页与桌面共用同一个关卡；网页版需要 WebGL 2。

```sh
godot --headless --path . --import
godot --headless --fixed-fps 60 --path . -- --test-level
```

自检覆盖六件餐具的可点击轮廓、鼠标与触摸、固定相机平移、提示、干扰道具、收纳计时、单一分类和通关。茶杯与杯碟是独立对象；先拿杯碟时，杯子由刚体模拟落回桌面。

## Blender 素材库

`art/room.blend` 同时是可编辑的关卡源文件和「茶点器物」收藏夹。六件餐具是已标记的 Blender Collection Assets，有独立原点和分类标签，直接从资产浏览器或 Append → Collection 复用。[制作说明](art/ASSETS.md)

房间光影用 Cycles 高采样烘焙并降噪。目标的待机、提示呼吸和收纳飞行共用同一张透明素材，像素轮廓也用于点击判定。实时模型只用于互动干扰道具，正确使用预乘透明合成。碰撞逻辑和画面分离，下一关可以按需要决定哪些支撑会动。

## 构建与发布

```sh
python3 tools/fetch-godot-web-template.py 4.7.2 /tmp/purrlock-web.zip
GODOT_WEB_TEMPLATE=/tmp/purrlock-web.zip sh tools/build-web.sh
node tools/test-worker.mjs
npx wrangler dev
```

GitHub Actions 构建与测试同一个关卡。Cloudflare 自动发布需要设置仓库的 Secret `CLOUDFLARE_API_TOKEN` 与 Variable `CLOUDFLARE_ACCOUNT_ID`。项目内中文字体授权见 `game/NotoSansCJK-OFL.txt`。iOS 真机尚未验证。
