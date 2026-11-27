# 福尔猫斯 · Purrlock Holmes

**案卷 01：午后客厅。** 拖动画面查看房间，找到并点击全部七件餐具。点中的物品会浮起，沿弧线落入猫爪收纳匣，落下才计数。没有倒计时、三消、相机旋转或视差。

## Godot / Blender

- 用 **Godot 4.7** 导入 `project.godot`，按 F5。支持鼠标左键和单指拖动/点按。桌面和 iOS 是目标平台，本 Demo 不含各平台安装包，也未验证 iOS 真机。微信小游戏不在本次范围。
- `art/room.blend` 是可编辑的原创场景。物品在 3D 中建模和摆放，镜头固定。运行时只绘制并平移同一张透视图，不实时渲染场景。
- `assets/pick.png` 是同机位的无遮挡像素编号图。它用 Blender 中实际几何算最前方物体；被家具盖住的区域不能隔空点到。用 Blender 4.3+ 重建：

  ```sh
  blender -b --python art/build_room.py
  ffmpeg -y -i assets/room.png -c:v libwebp -quality 89 assets/room.webp
  ```

  手动改过 .blend 时，保持镜头和分辨率一致，重新渲染美术图，再运行 `blender -b art/room.blend --python art/bake_pick.py`。

- Godot 自检：先在 Godot 中导入资源，然后运行 `godot --headless --path . -- --test-demo`。

## 浏览器试玩

网页是与 Godot 共用 Blender 烘焙和点击图的轻量 HTML/Canvas 版，不是 Godot Web 导出。Node 20+：

```sh
sh tools/build-web.sh
python3 -m http.server 8030 -d dist
```

打开 `http://localhost:8030`。

## Cloudflare 自动部署

`.github/workflows/cloudflare.yml` 在推送到 `main` 时先检查并构建网页，再部署到名为 `purrlock-holmes` 的 Cloudflare Worker。也可以在 Actions 手动运行。首次启用在 GitHub 仓库 **Settings → Secrets and variables → Actions** 设置：

- Secret `CLOUDFLARE_API_TOKEN`：用 Cloudflare 的 Workers 部署令牌，权限限定到目标账号；不要上传到 Git 或发送到聊天。
- Variable `CLOUDFLARE_ACCOUNT_ID`：目标 Cloudflare 账号的 Account ID。

未配置以上两项时，部署步骤会明确失败，不会假装发布成功。

### 收纳动画素材

使用相同的 Blender 镜头渲染无道具房间和七件透明道具后，再打包逐件清除和飞行动画所需的图集：

```sh
blender -b art/room.blend --python art/render_pickups.py
python3 art/pack_pickups.py  # 需要 Pillow
```

可用 `PURR_PICKUP_DIR` 指定中间图输出目录。游戏不会加载整张干净房间，只按实际收集状态叠放各件物品的局部背景。

### 分类提示与干扰道具

收纳匣上方仅显示本关目标类别和已收集数。提示会挑一个未收集目标，显示约三秒的呼吸与顺时针交错光线。点击可交互的干扰道具会短暂左右晃动；固定家具、房间背景、装饰和拖动不触发。

干扰项由 `art/render_wrong.py` 中的名单决定，不是所有场景模型。重新烘焙：

```sh
blender -b art/room.blend --python art/render_wrong.py
python3 art/pack_wrong.py  # 需要 Pillow
```
